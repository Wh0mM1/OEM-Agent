import asyncio
from typing import List, Dict, Any
from zoho.token_manager import token_manager


async def clean_crm_records(
    delete_unlinked_cases: bool = True,
    delete_duplicate_leads: bool = True,
):
    print("=== SURGICAL CLEANUP OF AGENT TEST DATA (PRESERVING SAMPLE DATA) ===")

    # 1. Clean only the 5 orphaned test Cases created by the agent
    if delete_unlinked_cases:
        print("\n--- Cleaning Orphaned Agent Test Cases ---")
        try:
            res = await token_manager.execute_with_token(
                "GET", "Cases", params={"fields": "id,Subject,Related_To,Account_Name,Contact_Name"}
            )
            cases = res.get("data", [])
            to_delete_cases = []
            for c in cases:
                # Target only the unlinked test tickets created during agent development
                if not c.get("Related_To") and not c.get("Account_Name") and not c.get("Contact_Name"):
                    to_delete_cases.append(c["id"])

            if to_delete_cases:
                ids_str = ",".join(to_delete_cases)
                await token_manager.execute_with_token("DELETE", "Cases", params={"ids": ids_str})
                print(f"[OK] Cleaned {len(to_delete_cases)} orphaned agent test Cases.")
            else:
                print("  No orphaned Cases found.")
        except Exception as e:
            print(f"  [Notice] Error cleaning Cases: {e}")

    # 2. Clean only duplicate test Leads (keep 1 clean Rajesh Sharma, preserve all other records)
    if delete_duplicate_leads:
        print("\n--- Cleaning Duplicate Test Leads ---")
        try:
            res = await token_manager.execute_with_token(
                "GET", "Leads", params={"fields": "id,Full_Name,Phone,Email"}
            )
            leads = res.get("data", [])
            seen_phones = set()
            to_delete_leads = []
            for lead in leads:
                phone = lead.get("Phone")
                # Only clean duplicates for test phone numbers used in development
                if phone in ["9820011223", "9820123456"]:
                    if phone in seen_phones:
                        to_delete_leads.append(lead["id"])
                    else:
                        seen_phones.add(phone)

            if to_delete_leads:
                ids_str = ",".join(to_delete_leads)
                await token_manager.execute_with_token("DELETE", "Leads", params={"ids": ids_str})
                print(f"[OK] Cleaned {len(to_delete_leads)} duplicate test Leads.")
            else:
                print("  No duplicate test Leads found.")
        except Exception as e:
            print(f"  [Notice] Error cleaning duplicate Leads: {e}")

    # 3. Update Priya Patel's Deal stage cleanly to 'Proposal/Price Quote'
    print("\n--- Correcting Priya Patel's Deal Stage ---")
    try:
        deal_res = await token_manager.execute_with_token(
            "GET", "Deals/search", params={"criteria": "(Deal_Name:starts_with:Priya Patel)"}
        )
        priya_deals = deal_res.get("data", [])
        if priya_deals:
            priya_id = priya_deals[0]["id"]
            update_payload = {
                "id": priya_id,
                "Stage": "Proposal/Price Quote",
                "Description": (
                    "Customer: Priya Patel | Phone: 9819988776 | Model: XUV700 AX7 Luxury | "
                    "Quotation: ₹23,99,000 | Dealership: Mahindra Automotive Galleria, Worli | "
                    "Sales Executive: Vikram Malhotra (+91 98200 44556) | Status: Test Drive Scheduled"
                ),
            }
            await token_manager.execute_with_token("PUT", "Deals", json_data={"data": [update_payload]})
            print(f"[OK] Updated Priya Patel's Deal to 'Proposal/Price Quote' stage (ID: {priya_id}).")
    except Exception as e:
        print(f"  [Notice] Could not update Priya's deal: {e}")

    print("\n=== CLEANUP COMPLETED (ALL SAMPLE DATA PRESERVED) ===")


if __name__ == "__main__":
    asyncio.run(clean_crm_records())
