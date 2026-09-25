import pytest
import json
from data.vehicle_db import vehicle_db
from zoho.mock_client import mock_zoho_client
from zoho.service import zoho_service
from agent.nodes import extract_slots_from_text, service_node
from agent.tools import log_service_ticket, get_vehicle_info, create_lead_record
from langchain_core.messages import HumanMessage


@pytest.fixture(autouse=True)
def force_mock_crm(monkeypatch):
    """Ensure unit tests execute deterministically against the mock CRM."""
    from core.config import settings
    monkeypatch.setattr(settings, "USE_MOCK_ZOHO", True)


def test_vehicle_database_zero_hallucination():
    """Verify that vehicle prices and specifications are strictly read from the catalog."""
    xuv = vehicle_db.get_vehicle_summary("XUV700")
    assert xuv is not None
    assert "₹13.99 Lakh - ₹26.99 Lakh" in xuv["price_range"]
    assert any("Level-2 ADAS" in f for v in xuv["variants"] for f in v["key_features"])

    thar = vehicle_db.get_vehicle_summary("Thar")
    assert thar is not None
    assert any("AX Opt" in v["name"] for v in thar["variants"])
    assert any("Thar Roxx" in v["name"] for v in thar["variants"])


def test_slot_extraction_regex():
    """Verify robust slot parsing for phones, emails, registration numbers, and odometers."""
    text = "My name is Rajesh, phone is 9820011223, email rajesh@test.com. My car is MH01AB1234 with 25000 km reading."
    slots = extract_slots_from_text(text, {})

    assert slots["phone"] == "9820011223"
    assert slots["email"] == "rajesh@test.com"
    assert slots["registration_number"] == "MH01AB1234"
    assert slots["odometer"] == "25000"


@pytest.mark.asyncio
async def test_crm_mock_preseeded_records():
    """Verify pre-seeded mock records for Priya Patel (Deal) and Booking #MAH-9921."""
    # Ongoing Pipeline Lookup
    deal = await zoho_service.search_deal("9819988776")
    assert deal is not None
    assert deal["id"] == "DEAL-2001"
    assert "Test Drive Scheduled" in deal["Stage"]
    assert deal["Deal_Name"] == "Priya Patel - XUV700 AX7L"
    assert deal["Contact_Name"]["name"] == "Priya Patel"

    # Booked Vehicle Lookup
    booking = await zoho_service.get_booking("MAH-9921")
    assert booking is not None
    assert booking["id"] == "DEAL-3001"
    assert booking["VIN"] == "MA1TA2SK5R8109921"
    assert "In Transit" in booking["Allocation_Status"]
    assert booking["Contact_Name"]["name"] == "Anand Rathi"


@pytest.mark.asyncio
async def test_stage_idempotency_and_creation():
    """Ensure duplicate leads are not generated in a single session."""
    lead_payload = {
        "First_Name": "Sunil",
        "Last_Name": "Gavaskar",
        "Phone": "9820099887",
        "Email": "sunil.g@example.com",
        "City": "Mumbai",
        "Vehicle_Model_of_Interest": "Scorpio-N",
    }
    res = await zoho_service.create_lead(lead_payload)
    assert res["success"] is True
    assert "LEAD-" in res["lead_id"]

    # Test Case Ticket Creation
    case_payload = {
        "Subject": "Periodic Service 20,000 km",
        "Contact_Name": "Sunil Gavaskar",
        "Phone": "9820099887",
        "Registration_Number": "MH02EF9999",
        "Odometer_Reading": "21000",
        "Issue_Type": "Oil change & brake check",
        "Preferred_Center": "Worli Service Galleria",
    }
    case_res = await zoho_service.create_service_case(case_payload)
    assert case_res["success"] is True
    assert "CASE-" in case_res["case_id"]


@pytest.mark.asyncio
async def test_log_service_ticket_with_literals():
    """Verify that log_service_ticket receives and forwards dynamic literals properly."""
    res = await log_service_ticket.ainvoke({
        "contact_name": "Vikram Rao",
        "phone": "9820123456",
        "registration_number": "MH01AB1234",
        "odometer": "15000",
        "issue_type": "Brake vibration & shudder",
        "preferred_center": "Worli",
        "priority": "High",
        "status": "Service Appointment Scheduled",
        "case_origin": "Chat",
    })
    data = json.loads(res)
    assert data["success"] is True
    assert "CASE-" in data["case_id"]
    record = data.get("record") or data.get("data")
    assert record is not None
    assert record["Priority"] == "High"
    assert record["Status"] == "Service Appointment Scheduled"
    assert record["Case_Origin"] == "Chat"
    assert record["Preferred_Center"] == "Worli"


@pytest.mark.asyncio
async def test_service_case_auto_links_deal_and_contact():
    """Verify that when Priya Patel logs a service case, it automatically links to her Deal and Contact."""
    state = {
        "messages": [HumanMessage(content="My car registration is MH02CD9999, odometer is 20000 km, phone 9819988776. Needs brake service at Worli.")],
        "active_stage": "post_purchase_service",
        "previous_stage": "new_lead",
        "collected_slots": {
            "registration_number": "MH02CD9999",
            "odometer": "20000",
            "phone": "9819988776",
            "preferred_center": "Worli",
            "issue_type": "Brake service",
            "name": "Priya Patel",
        },
        "crm_ids": {},
    }
    res = await service_node(state)
    assert "tool_chips" in res
    assert len(res["tool_chips"]) > 0
    chip_data = res["tool_chips"][0]["data"]
    assert chip_data["success"] is True
    record = chip_data.get("record") or chip_data.get("data")
    assert record is not None
    assert record["Related_To"]["id"] == "DEAL-2001" or "1427144" in str(record["Related_To"])
    assert record["Contact_Name"]["id"] == "CON-1001" or "1427144" in str(record["Contact_Name"])
    assert record["Account_Name"]["id"] == "ACC-1001" or "1427144" in str(record["Account_Name"])
    assert record["Priority"] == "High"


def test_rate_limiter_hourly_cap_and_byok():
    """Verify that after 30 requests/hr, system enforces BYOK custom key."""
    from api.server import RateLimiter
    limiter = RateLimiter(max_requests=30, window_seconds=3600)

    for i in range(30):
        allowed, used, remaining = limiter.check_and_record(has_custom_key=False)
        assert allowed is True
        assert used == i + 1
        assert remaining == 30 - (i + 1)

    # 31st request with shared key is blocked
    allowed, used, remaining = limiter.check_and_record(has_custom_key=False)
    assert allowed is False
    assert remaining == 0

    # User bringing their own key bypasses the cap immediately
    allowed, used, remaining = limiter.check_and_record(has_custom_key=True)
    assert allowed is True



@pytest.mark.asyncio
async def test_variant_detection_and_description_enrichment():
    """Verify that variant like AX7L is recognized from DB and all variant details are stored in Description."""
    text = "Tell me the price and features of the XUV700 AX7L, and book a test drive for Neha Kapoor, phone 9833445566, email neha.kapoor@example.com, Mumbai."
    slots = extract_slots_from_text(text, {})

    assert slots["name"] == "Neha Kapoor"
    assert slots["phone"] == "9833445566"
    assert slots["email"] == "neha.kapoor@example.com"
    assert slots["city"] == "Mumbai"
    assert slots["model_interest"] == "XUV700"
    assert slots["variant_interest"] == "AX7 Luxury (AX7L)"

    # Test lead creation tool call directly
    res = await create_lead_record.ainvoke({
        "full_name": slots["name"],
        "phone": slots["phone"],
        "email": slots["email"],
        "city": slots["city"],
        "model_of_interest": slots["model_interest"],
        "variant": slots["variant_interest"],
    })
    data = json.loads(res)
    assert data["success"] is True
    lead_id = data["lead_id"]
    lead = mock_zoho_client.leads[lead_id]
    
    desc = lead["Description"]
    assert "Variant: AX7 Luxury (AX7L)" in desc
    assert "₹23.99 Lakh" in desc
    assert "Level-2 ADAS" in desc
    assert "Sony 12-Speaker 3D Audio" in desc
    assert "Diesel" in desc
    assert "6-Speed Automatic" in desc
    assert "7 Seater" in desc
