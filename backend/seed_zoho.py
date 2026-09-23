import asyncio
from typing import Optional, Dict, Any, List
from zoho.token_manager import token_manager


async def get_or_create_account(account_name: str, phone: str) -> Optional[str]:
    """Finds existing account or creates a new one in Zoho CRM."""
    try:
        search_res = await token_manager.execute_with_token(
            "GET", "Accounts/search", params={"criteria": f"(Account_Name:equals:{account_name})"}
        )
        records = search_res.get("data", [])
        if records:
            print(f"  [Found Existing Account] {account_name} (ID: {records[0]['id']})")
            return records[0]["id"]
    except Exception:
        pass

    try:
        payload = {"Account_Name": account_name, "Phone": phone}
        res = await token_manager.execute_with_token("POST", "Accounts", json_data={"data": [payload]})
        records = res.get("data", [])
        if records and records[0].get("code") == "SUCCESS":
            acc_id = records[0]["details"]["id"]
            print(f"  [Created Account] {account_name} (ID: {acc_id})")
            return acc_id
    except Exception as e:
        print(f"  [Account Creation Notice] {e}")
    return None


async def get_or_create_contact(
    first_name: str, last_name: str, phone: str, email: str, account_id: Optional[str] = None
) -> Optional[str]:
    """Finds existing contact by phone or creates a new one in Zoho CRM."""
    try:
        search_res = await token_manager.execute_with_token(
            "GET", "Contacts/search", params={"phone": phone}
        )
        records = search_res.get("data", [])
        if records:
            print(f"  [Found Existing Contact] {first_name} {last_name} (ID: {records[0]['id']})")
            return records[0]["id"]
    except Exception:
        pass

    try:
        payload: Dict[str, Any] = {
            "First_Name": first_name,
            "Last_Name": last_name,
            "Phone": phone,
            "Email": email,
        }
        if account_id:
            payload["Account_Name"] = {"id": account_id}
        res = await token_manager.execute_with_token("POST", "Contacts", json_data={"data": [payload]})
        records = res.get("data", [])
        if records and records[0].get("code") == "SUCCESS":
            con_id = records[0]["details"]["id"]
            print(f"  [Created Contact] {first_name} {last_name} (ID: {con_id})")
            return con_id
    except Exception as e:
        print(f"  [Contact Creation Notice] {e}")
    return None


async def seed_live_zoho():
    print("=== SEEDING LIVE ZOHO CRM PORTAL ===")

    # 1. Seed Lead: Rajesh Sharma
    print("\n--- Seeding Rajesh Sharma (Lead) ---")
    lead_payload = {
        "First_Name": "Rajesh",
        "Last_Name": "Sharma",
        "Phone": "9820011223",
        "Email": "rajesh.sharma@example.com",
        "City": "Mumbai",
        "Company": "Retail Customer",
        "Lead_Source": "Mahindra AI Digital Showroom",
        "Lead_Status": "New",
        "Vehicle_Model_of_Interest": "Thar",
        "Description": "Interested in Mahindra Thar AX Opt / 4x4. Exploring variant pricing and test drive in Mumbai.",
    }
    try:
        res = await token_manager.execute_with_token("POST", "Leads", json_data={"data": [lead_payload]})
        data = res.get("data", [{}])[0]
        if data.get("code") == "SUCCESS":
            lead_id = data["details"]["id"]
            print(f"[OK] Lead Created: Rajesh Sharma (ID: {lead_id})")
        else:
            print(f"[WARN] Lead creation response: {res}")
    except Exception as e:
        print(f"[ERROR] Lead creation failed: {e}")

    # 2. Seed Contact & Deal 1: Priya Patel (Ongoing Pipeline)
    print("\n--- Seeding Priya Patel (Deal & Contact) ---")
    account1_id = await get_or_create_account("Priya Patel", "9819988776")
    contact1_id = await get_or_create_contact("Priya", "Patel", "9819988776", "priya.patel@example.com", account1_id)

    deal1_payload: Dict[str, Any] = {
        "Deal_Name": "Priya Patel - XUV700 AX7L",
        "Stage": "Proposal/Price Quote",
        "Amount": 2399000,
        "Closing_Date": "2026-10-31",
        "Type": "New Business",
        "Lead_Source": "Mahindra AI Digital Showroom",
        "Description": "Customer: Priya Patel. Phone: 9819988776. Model: XUV700 AX7 Luxury. Dealership: Mahindra Automotive Galleria, Worli. Sales Executive: Vikram Malhotra (+91 98200 44556). Status: Test Drive Scheduled for 26th September at 11:00 AM. Follow-up: WhatsApp requested.",
    }
    if contact1_id:
        deal1_payload["Contact_Name"] = {"id": contact1_id}
    if account1_id:
        deal1_payload["Account_Name"] = {"id": account1_id}

    # Check if deal already exists for Priya Patel using word or starts_with
    existing_deals: List[Dict[str, Any]] = []
    if contact1_id:
        try:
            res = await token_manager.execute_with_token(
                "GET", "Deals/search", params={"criteria": f"(Contact_Name:equals:{contact1_id})"}
            )
            existing_deals = res.get("data", [])
        except Exception:
            pass

    if not existing_deals:
        try:
            res = await token_manager.execute_with_token(
                "GET", "Deals/search", params={"word": "Priya Patel"}
            )
            existing_deals = res.get("data", [])
        except Exception:
            pass

    if not existing_deals:
        try:
            res = await token_manager.execute_with_token(
                "GET", "Deals/search", params={"criteria": "(Deal_Name:starts_with:Priya Patel)"}
            )
            existing_deals = res.get("data", [])
        except Exception:
            pass

    try:
        if existing_deals:
            deal_id = existing_deals[0]["id"]
            update_payload = {"id": deal_id, **deal1_payload}
            await token_manager.execute_with_token("PUT", "Deals", json_data={"data": [update_payload]})
            print(f"[OK] Existing Deal Updated to Clean Name & Contact/Account Link: (ID: {deal_id})")
        else:
            res = await token_manager.execute_with_token("POST", "Deals", json_data={"data": [deal1_payload]})
            data = res.get("data", [{}])[0]
            if data.get("code") == "SUCCESS":
                deal1_id = data["details"]["id"]
                print(f"[OK] Pipeline Deal Created: Priya Patel - XUV700 AX7L (ID: {deal1_id})")
            else:
                print(f"[WARN] Pipeline Deal creation response: {res}")
    except Exception as e:
        print(f"[ERROR] Pipeline Deal failed: {e}")

    # 3. Seed Contact & Deal 2: Anand Rathi (Booked Vehicle #MAH-9921)
    print("\n--- Seeding Anand Rathi (Booking Deal & Contact) ---")
    account2_id = await get_or_create_account("Anand Rathi", "9822334455")
    contact2_id = await get_or_create_contact("Anand", "Rathi", "9822334455", "anand.rathi@example.com", account2_id)

    deal2_payload: Dict[str, Any] = {
        "Deal_Name": "Booking #MAH-9921 - Scorpio-N Z8L",
        "Stage": "Closed Won",
        "Amount": 2454000,
        "Closing_Date": "2026-10-15",
        "Type": "Existing Business",
        "Lead_Source": "Mahindra AI Digital Showroom",
        "Description": "Booking Reference: MAH-9921. Customer: Anand Rathi. Phone: 9822334455. Model: Scorpio-N Z8L 4XPLOR Diesel AT. Allocation Status: In Transit from Chakan Plant. VIN: MA1TA2SK5R8109921. Expected Delivery: October 8, 2026. Balance Due: ₹18,50,000. Delivery Center: Mahindra Apex Center, Andheri West.",
    }
    if contact2_id:
        deal2_payload["Contact_Name"] = {"id": contact2_id}
    if account2_id:
        deal2_payload["Account_Name"] = {"id": account2_id}

    existing_bookings: List[Dict[str, Any]] = []
    if contact2_id:
        try:
            res = await token_manager.execute_with_token(
                "GET", "Deals/search", params={"criteria": f"(Contact_Name:equals:{contact2_id})"}
            )
            existing_bookings = res.get("data", [])
        except Exception:
            pass

    if not existing_bookings:
        try:
            res = await token_manager.execute_with_token(
                "GET", "Deals/search", params={"word": "MAH-9921"}
            )
            existing_bookings = res.get("data", [])
        except Exception:
            pass

    if not existing_bookings:
        try:
            res = await token_manager.execute_with_token(
                "GET", "Deals/search", params={"criteria": "(Deal_Name:starts_with:Booking #MAH-9921)"}
            )
            existing_bookings = res.get("data", [])
        except Exception:
            pass

    try:
        if existing_bookings:
            deal_id = existing_bookings[0]["id"]
            update_payload = {"id": deal_id, **deal2_payload}
            await token_manager.execute_with_token("PUT", "Deals", json_data={"data": [update_payload]})
            print(f"[OK] Existing Booking Deal Updated with Contact/Account Link: (ID: {deal_id})")
        else:
            res = await token_manager.execute_with_token("POST", "Deals", json_data={"data": [deal2_payload]})
            data = res.get("data", [{}])[0]
            if data.get("code") == "SUCCESS":
                deal2_id = data["details"]["id"]
                print(f"[OK] Booking Deal Created: #MAH-9921 (ID: {deal2_id})")
            else:
                print(f"[WARN] Booking Deal creation response: {res}")
    except Exception as e:
        print(f"[ERROR] Booking Deal failed: {e}")

    print("\n=== LIVE SEEDING COMPLETED ===")


if __name__ == "__main__":
    asyncio.run(seed_live_zoho())
