from typing import Dict, Any, Optional, List
from zoho.token_manager import token_manager


class LiveZohoClient:
    """Production client executing real Zoho CRM v8 REST API operations with relational interlinks."""

    async def search_contact_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """Searches Contacts by phone number."""
        clean_phone = phone.strip().replace("+", "").replace("-", "").replace(" ", "")
        try:
            res = await token_manager.execute_with_token(
                "GET",
                "Contacts/search",
                params={"phone": clean_phone},
            )
            contacts = res.get("data", [])
            if contacts:
                return contacts[0]
        except Exception:
            pass
        return None

    async def get_or_create_account(self, account_name: str, phone: str) -> Optional[str]:
        """Finds or creates an Account record for the customer."""
        if not account_name:
            return None
        clean_name = account_name.strip()
        try:
            res = await token_manager.execute_with_token(
                "GET", "Accounts/search", params={"criteria": f"(Account_Name:equals:{clean_name})"}
            )
            records = res.get("data", [])
            if records:
                return records[0]["id"]
        except Exception:
            pass

        try:
            payload = {"Account_Name": clean_name, "Phone": phone}
            res = await token_manager.execute_with_token("POST", "Accounts", json_data={"data": [payload]})
            records = res.get("data", [])
            if records and records[0].get("code") == "SUCCESS":
                return records[0]["details"]["id"]
        except Exception:
            pass
        return None

    async def get_or_create_contact(
        self, contact_name: str, phone: str, email: Optional[str] = None, account_id: Optional[str] = None
    ) -> Optional[str]:
        """Finds or creates a Contact record, linking it to the Account."""
        if not phone:
            return None
        existing = await self.search_contact_by_phone(phone)
        if existing:
            return existing["id"]

        parts = (contact_name or "Vehicle Owner").strip().split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else "Owner"

        payload: Dict[str, Any] = {
            "First_Name": first_name,
            "Last_Name": last_name,
            "Phone": phone.strip().replace("+", "").replace("-", "").replace(" ", ""),
        }
        if email:
            payload["Email"] = email
        if account_id:
            payload["Account_Name"] = {"id": account_id}

        try:
            res = await token_manager.execute_with_token("POST", "Contacts", json_data={"data": [payload]})
            records = res.get("data", [])
            if records and records[0].get("code") == "SUCCESS":
                return records[0]["details"]["id"]
        except Exception:
            pass
        return None

    async def add_deal_note(self, deal_id: str, title: str, content: str) -> Optional[Dict[str, Any]]:
        """Attaches a timeline Note to a Deal record for activity tracking."""
        payload = {
            "data": [
                {
                    "Note_Title": title,
                    "Note_Content": content,
                    "Parent_Id": deal_id,
                    "se_module": "Deals",
                }
            ]
        }
        try:
            return await token_manager.execute_with_token("POST", "Notes", json_data=payload)
        except Exception:
            return None

    async def create_lead(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a Lead in Zoho CRM, interlinking with existing customer context if recognized."""
        enriched = dict(payload)
        phone = payload.get("Phone")

        # Interlink check: If customer already exists in Contacts, annotate the lead description
        if phone:
            try:
                contact = await self.search_contact_by_phone(phone)
                if contact:
                    c_name = f"{contact.get('First_Name', '')} {contact.get('Last_Name', '')}".strip()
                    desc = enriched.get("Description", "")
                    enriched["Description"] = f"{desc} | [CRM Interlink: Existing Customer Contact #{contact['id']} ({c_name})]"
            except Exception:
                pass

        body = {"data": [enriched]}
        res = await token_manager.execute_with_token("POST", "Leads", json_data=body)
        records = res.get("data", [])
        if records and records[0].get("code") == "SUCCESS":
            return {
                "success": True,
                "lead_id": records[0]["details"]["id"],
                "message": "Lead created successfully in Zoho CRM.",
                "data": enriched,
            }
        return {"success": False, "raw": res}

    async def search_deal_by_phone_or_id(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Searches Deals by Deal ID, linked Contact phone, or search word."""
        clean_id = identifier.strip().replace("+", "").replace("-", "").replace(" ", "")

        # 1. Try direct Deal lookup if it looks like an ID
        if clean_id.isdigit() and len(clean_id) > 10:
            try:
                res = await token_manager.execute_with_token(
                    "GET",
                    f"Deals/{clean_id}",
                    params={"fields": "id,Deal_Name,Stage,Amount,Description,Closing_Date,Contact_Name,Account_Name"},
                )
                deals = res.get("data", [])
                if deals:
                    return deals[0]
            except Exception:
                pass

        # 2. Search Contacts by phone to find associated Deal
        if clean_id.isdigit() and len(clean_id) == 10:
            try:
                contact = await self.search_contact_by_phone(clean_id)
                if contact:
                    contact_id = contact["id"]
                    deals_res = await token_manager.execute_with_token(
                        "GET",
                        "Deals/search",
                        params={
                            "criteria": f"(Contact_Name:equals:{contact_id})",
                            "fields": "id,Deal_Name,Stage,Amount,Description,Closing_Date,Contact_Name,Account_Name",
                        },
                    )
                    deals = deals_res.get("data", [])
                    if deals:
                        deal = deals[0]
                        deal["Contact_Details"] = contact
                        return deal
            except Exception:
                pass

        # 3. Search Deals via `word` parameter (Zoho does not support 'contains' operator in criteria)
        try:
            res = await token_manager.execute_with_token(
                "GET",
                "Deals/search",
                params={
                    "word": clean_id,
                    "fields": "id,Deal_Name,Stage,Amount,Description,Closing_Date,Contact_Name,Account_Name",
                },
            )
            deals = res.get("data", [])
            if deals:
                return deals[0]
        except Exception:
            pass

        # 4. Search Deals via starts_with criteria
        try:
            res = await token_manager.execute_with_token(
                "GET",
                "Deals/search",
                params={
                    "criteria": f"(Deal_Name:starts_with:{clean_id})",
                    "fields": "id,Deal_Name,Stage,Amount,Description,Closing_Date,Contact_Name,Account_Name",
                },
            )
            deals = res.get("data", [])
            if deals:
                return deals[0]
        except Exception:
            pass

        return None

    async def update_deal(self, deal_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Updates an existing Deal record in Zoho CRM and logs an activity Note."""
        payload = {"data": [{"id": deal_id, **updates}]}
        res = await token_manager.execute_with_token("PUT", "Deals", json_data=payload)

        # Log timeline note if follow-up preference was updated
        pref = updates.get("Follow_Up_Preference") or updates.get("Description")
        if pref:
            await self.add_deal_note(
                deal_id=deal_id,
                title="Customer Preference Updated via AI",
                content=f"Updated preference setting: {pref}",
            )

        return {"success": True, "deal_id": deal_id, "updated_fields": updates, "raw": res}

    async def get_booking_deal(self, booking_id_or_phone: str) -> Optional[Dict[str, Any]]:
        """Searches for a Deal in 'Closed Won' stage with custom Booking criteria."""
        query = booking_id_or_phone.strip()
        clean_phone = query.replace("+", "").replace("-", "").replace(" ", "")

        # 1. Search Contact by phone if query is 10-digit number
        if clean_phone.isdigit() and len(clean_phone) == 10:
            try:
                contact = await self.search_contact_by_phone(clean_phone)
                if contact:
                    contact_id = contact["id"]
                    deals_res = await token_manager.execute_with_token(
                        "GET",
                        "Deals/search",
                        params={
                            "criteria": f"(Contact_Name:equals:{contact_id})",
                            "fields": "id,Deal_Name,Stage,Amount,Description,Closing_Date,Contact_Name,Account_Name",
                        },
                    )
                    deals = deals_res.get("data", [])
                    if deals:
                        return deals[0]
            except Exception:
                pass

        # 2. Search Deals using `word` parameter
        try:
            res = await token_manager.execute_with_token(
                "GET",
                "Deals/search",
                params={
                    "word": query,
                    "fields": "id,Deal_Name,Stage,Amount,Description,Closing_Date,Contact_Name,Account_Name",
                },
            )
            deals = res.get("data", [])
            if deals:
                return deals[0]
        except Exception:
            pass

        # 3. Search Deals criteria using starts_with
        try:
            res = await token_manager.execute_with_token(
                "GET",
                "Deals/search",
                params={
                    "criteria": f"(Deal_Name:starts_with:{query})",
                    "fields": "id,Deal_Name,Stage,Amount,Description,Closing_Date,Contact_Name,Account_Name",
                },
            )
            deals = res.get("data", [])
            if deals:
                return deals[0]
        except Exception:
            pass
        return None

    async def create_service_case(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a ticket in the Cases module, with complete auto-interlinking:
        - Deal_Name (Deal lookup in Zoho CRM Cases)
        - Related_To (Contact lookup in Zoho CRM Cases)
        - Account_Name (Account lookup in Zoho CRM Cases)
        """
        enriched_payload = dict(payload)
        phone = payload.get("Phone")
        contact_name = payload.get("Contact_Name_Text") or payload.get("contact_name")

        deal_id = None
        if "Deal_Name" in enriched_payload:
            val = enriched_payload["Deal_Name"]
            deal_id = val.get("id") if isinstance(val, dict) else val
        elif "Related_To" in enriched_payload:
            val = enriched_payload.pop("Related_To")
            deal_id = val.get("id") if isinstance(val, dict) else val

        contact_id = None
        if "Contact_Name" in enriched_payload:
            val = enriched_payload.pop("Contact_Name")
            contact_id = val.get("id") if isinstance(val, dict) else val

        # 1. Resolve Deal, Contact, and Account by phone if missing
        if phone:
            try:
                deal = await self.search_deal_by_phone_or_id(phone)
                if deal:
                    if not deal_id:
                        deal_id = deal.get("id")
                    if not contact_id and deal.get("Contact_Name"):
                        c_val = deal["Contact_Name"]
                        contact_id = c_val["id"] if isinstance(c_val, dict) else c_val
                    if "Account_Name" not in enriched_payload and deal.get("Account_Name"):
                        a_val = deal["Account_Name"]
                        a_id = a_val["id"] if isinstance(a_val, dict) else a_val
                        enriched_payload["Account_Name"] = {"id": a_id}
            except Exception:
                pass

        # 2. If Contact_Name or Account_Name still missing, auto-create Contact & Account on the fly
        if phone and (not contact_id or "Account_Name" not in enriched_payload):
            try:
                account_id = (
                    enriched_payload.get("Account_Name", {}).get("id")
                    if isinstance(enriched_payload.get("Account_Name"), dict)
                    else None
                )
                if not account_id and contact_name:
                    account_id = await self.get_or_create_account(contact_name, phone)
                    if account_id:
                        enriched_payload["Account_Name"] = {"id": account_id}

                if not contact_id:
                    contact_id = await self.get_or_create_contact(
                        contact_name=contact_name or "Vehicle Owner",
                        phone=phone,
                        account_id=account_id,
                    )
            except Exception:
                pass

        if deal_id:
            enriched_payload["Deal_Name"] = {"id": deal_id}
        if contact_id:
            enriched_payload["Related_To"] = {"id": contact_id}

        # Clean temporary helper keys before API submission
        enriched_payload.pop("Contact_Name_Text", None)
        enriched_payload.pop("contact_name", None)

        body = {"data": [enriched_payload]}
        res = await token_manager.execute_with_token("POST", "Cases", json_data=body)
        records = res.get("data", [])
        if records and records[0].get("code") == "SUCCESS":
            return {
                "success": True,
                "case_id": records[0]["details"]["id"],
                "message": "Service case created in Zoho CRM.",
                "record": enriched_payload,
                "data": enriched_payload,
            }
        return {"success": False, "raw": res}
