import uuid
from typing import Dict, Any, Optional, List


class MockZohoClient:
    """In-memory simulation of Zoho CRM v8 REST endpoints.
    
    Enables immediate offline validation and zero-cost test runs.
    """

    def __init__(self):
        self.contacts: Dict[str, Dict[str, Any]] = {
            "CON-1001": {
                "id": "CON-1001",
                "First_Name": "Priya",
                "Last_Name": "Patel",
                "Full_Name": "Priya Patel",
                "Phone": "9819988776",
                "Email": "priya.patel@example.com",
            },
            "CON-2001": {
                "id": "CON-2001",
                "First_Name": "Anand",
                "Last_Name": "Rathi",
                "Full_Name": "Anand Rathi",
                "Phone": "9822334455",
                "Email": "anand.rathi@example.com",
            },
        }

        self.accounts: Dict[str, Dict[str, Any]] = {
            "ACC-1001": {"id": "ACC-1001", "Account_Name": "Priya Patel", "Phone": "9819988776"},
            "ACC-2001": {"id": "ACC-2001", "Account_Name": "Anand Rathi", "Phone": "9822334455"},
        }

        self.leads: Dict[str, Dict[str, Any]] = {
            "LEAD-1001": {
                "id": "LEAD-1001",
                "Full_Name": "Rajesh Sharma",
                "First_Name": "Rajesh",
                "Last_Name": "Sharma",
                "Phone": "9820011223",
                "Email": "rajesh.sharma@example.com",
                "City": "Mumbai",
                "Vehicle_Model_of_Interest": "Thar",
                "Lead_Source": "AI Chat Agent",
                "Lead_Status": "Contacted",
            }
        }

        self.deals: Dict[str, Dict[str, Any]] = {
            "DEAL-2001": {
                "id": "DEAL-2001",
                "Deal_Name": "Priya Patel - XUV700 AX7L",
                "Contact_Name": {"id": "CON-1001", "name": "Priya Patel"},
                "Account_Name": {"id": "ACC-1001", "name": "Priya Patel"},
                "Customer_Name": "Priya Patel",
                "Phone": "9819988776",
                "Email": "priya.patel@example.com",
                "Model": "XUV700",
                "Variant": "AX7 Luxury",
                "Stage": "Test Drive Scheduled",
                "Scheduled_Date": "2026-09-26 11:00 AM",
                "Quotation_Amount": "₹23,99,000",
                "Assigned_Dealer": "Mahindra Automotive Galleria, Worli",
                "Sales_Executive": "Vikram Malhotra (+91 98200 44556)",
                "Follow_Up_Preference": "WhatsApp Confirmation Requested",
                "Description": "Customer: Priya Patel. Phone: 9819988776. Model: XUV700 AX7 Luxury. Dealership: Mahindra Automotive Galleria, Worli. Sales Executive: Vikram Malhotra (+91 98200 44556). Status: Test Drive Scheduled for 26th September at 11:00 AM. Follow-up: WhatsApp requested.",
            },
            "DEAL-3001": {
                "id": "DEAL-3001",
                "Booking_ID": "MAH-9921",
                "Deal_Name": "Booking #MAH-9921 - Scorpio-N Z8L",
                "Contact_Name": {"id": "CON-2001", "name": "Anand Rathi"},
                "Account_Name": {"id": "ACC-2001", "name": "Anand Rathi"},
                "Customer_Name": "Anand Rathi",
                "Phone": "9822334455",
                "Email": "anand.rathi@example.com",
                "Model": "Scorpio-N",
                "Variant": "Z8L 4XPLOR Diesel Automatic",
                "Color": "Deep Forest Metallic",
                "Stage": "Closed Won - Booking Done",
                "Allocation_Status": "In Transit from Chakan Plant",
                "VIN": "MA1TA2SK5R8109921",
                "Expected_Delivery": "October 8, 2026",
                "Balance_Amount": "₹18,50,000",
                "Delivery_Dealership": "Mahindra Apex Center, Andheri West",
                "Description": "Booking Reference: MAH-9921. Customer: Anand Rathi. Phone: 9822334455. Model: Scorpio-N Z8L 4XPLOR Diesel AT. Allocation Status: In Transit from Chakan Plant. VIN: MA1TA2SK5R8109921. Expected Delivery: October 8, 2026. Balance Due: ₹18,50,000. Delivery Center: Mahindra Apex Center, Andheri West.",
            },
        }

        self.cases: Dict[str, Dict[str, Any]] = {}

    async def get_or_create_account(self, account_name: str, phone: str) -> str:
        for acc_id, acc in self.accounts.items():
            if acc.get("Account_Name") == account_name or acc.get("Phone") == phone:
                return acc_id
        acc_id = f"ACC-{uuid.uuid4().hex[:4].upper()}"
        self.accounts[acc_id] = {"id": acc_id, "Account_Name": account_name, "Phone": phone}
        return acc_id

    async def get_or_create_contact(
        self, contact_name: str, phone: str, account_id: Optional[str] = None
    ) -> str:
        clean = phone.strip().replace(" ", "").replace("-", "")
        for con_id, con in self.contacts.items():
            if con.get("Phone") == clean:
                return con_id
        con_id = f"CON-{uuid.uuid4().hex[:4].upper()}"
        parts = contact_name.strip().split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else "Owner"
        self.contacts[con_id] = {
            "id": con_id,
            "First_Name": first_name,
            "Last_Name": last_name,
            "Full_Name": contact_name,
            "Phone": clean,
            "Account_Name": {"id": account_id} if account_id else None,
        }
        return con_id

    async def create_lead(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        lead_id = f"LEAD-{uuid.uuid4().hex[:6].upper()}"
        phone = payload.get("Phone")
        enriched = dict(payload)

        # CRM Interlink: annotate if existing customer contact exists
        if phone:
            contact = await self.search_contact_by_phone(phone)
            if contact:
                desc = enriched.get("Description", "")
                enriched["Description"] = f"{desc} | [CRM Interlink: Existing Customer Contact #{contact['id']}]"

        record = {"id": lead_id, **enriched, "Lead_Source": "AI Conversational Agent", "Lead_Status": "New"}
        self.leads[lead_id] = record
        return {"success": True, "lead_id": lead_id, "record": record}

    async def search_contact_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        clean = phone.strip().replace(" ", "").replace("-", "")
        for con in self.contacts.values():
            if clean in con.get("Phone", ""):
                return con
        return None

    async def search_deal_by_phone_or_id(self, identifier: str) -> Optional[Dict[str, Any]]:
        clean = identifier.strip().replace(" ", "").replace("-", "").upper()
        for deal_id, deal in self.deals.items():
            if deal_id == clean or clean in deal.get("Booking_ID", "").upper():
                return deal
            if clean in deal.get("Phone", "") or clean in deal.get("Customer_Name", "").upper():
                return deal
            if clean in deal.get("Deal_Name", "").upper() or clean in deal.get("Description", "").upper():
                return deal
        return None

    async def update_deal(self, deal_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        if deal_id in self.deals:
            self.deals[deal_id].update(updates)
            return {"success": True, "deal_id": deal_id, "updated": self.deals[deal_id]}
        return {"success": False, "error": f"Deal ID {deal_id} not found"}

    async def get_booking_deal(self, booking_id_or_phone: str) -> Optional[Dict[str, Any]]:
        clean = booking_id_or_phone.strip().replace(" ", "").upper()
        for deal in self.deals.values():
            if clean in deal.get("Booking_ID", "").upper() or clean in deal.get("Phone", ""):
                return deal
        return None

    async def create_service_case(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        case_id = f"CASE-{uuid.uuid4().hex[:5].upper()}"
        enriched = dict(payload)
        phone = payload.get("Phone")
        contact_name = payload.get("Contact_Name_Text") or payload.get("Contact_Name") or "Vehicle Owner"
        if isinstance(contact_name, dict):
            contact_name = contact_name.get("name", "Vehicle Owner")

        # 1. Auto-link Related_To, Contact_Name, Account_Name in mock if matching deal exists
        if phone:
            deal = await self.search_deal_by_phone_or_id(phone)
            if deal:
                if "Related_To" not in enriched:
                    enriched["Related_To"] = {"id": deal["id"], "name": deal.get("Deal_Name")}
                if "Contact_Name" not in enriched and deal.get("Contact_Name"):
                    enriched["Contact_Name"] = deal["Contact_Name"]
                if "Account_Name" not in enriched and deal.get("Account_Name"):
                    enriched["Account_Name"] = deal["Account_Name"]

        # 2. If Contact_Name or Account_Name still not linked, auto-create Contact & Account
        if phone and ("Contact_Name" not in enriched or "Account_Name" not in enriched):
            acc_id = await self.get_or_create_account(contact_name, phone)
            con_id = await self.get_or_create_contact(contact_name, phone, acc_id)
            if "Account_Name" not in enriched:
                enriched["Account_Name"] = {"id": acc_id, "name": contact_name}
            if "Contact_Name" not in enriched:
                enriched["Contact_Name"] = {"id": con_id, "name": contact_name}

        enriched.pop("Contact_Name_Text", None)

        record = {
            "id": case_id,
            "Case_Number": case_id,
            "Status": "Service Appointment Scheduled",
            "Priority": "Medium",
            **enriched,
        }
        self.cases[case_id] = record
        return {"success": True, "case_id": case_id, "record": record}

    def inspect_database(self) -> Dict[str, Any]:
        return {
            "leads": list(self.leads.values()),
            "contacts": list(self.contacts.values()),
            "accounts": list(self.accounts.values()),
            "deals": list(self.deals.values()),
            "cases": list(self.cases.values()),
        }


mock_zoho_client = MockZohoClient()
