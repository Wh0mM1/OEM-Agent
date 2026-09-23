import json
from typing import Dict, Any, Optional, Literal, Annotated
from langchain_core.tools import tool
from data.vehicle_db import vehicle_db
from zoho.service import zoho_service


@tool
def get_vehicle_info(
    model_name: Annotated[
        Literal["XUV700", "Thar", "Scorpio-N", "Bolero Neo"],
        "Authoritative Mahindra vehicle model name to inspect specs and pricing.",
    ],
    variant_name: Annotated[
        Optional[str],
        "Optional trim or variant name (e.g., 'AX7L', 'Z8L', 'LX', 'AX Opt') for granular technical specifications and ex-showroom price.",
    ] = None,
) -> str:
    """Retrieves verified specifications, variant details, and ex-showroom pricing for Mahindra vehicles.
    
    Args:
        model_name: Name of the model ('XUV700', 'Thar', 'Scorpio-N', 'Bolero Neo').
        variant_name: Optional specific variant (e.g., 'AX7L', 'Z8L', 'LX').
    """
    summary = vehicle_db.get_vehicle_summary(model_name)
    if not summary:
        models = vehicle_db.list_all_models()
        return f"Model '{model_name}' not found. Available models are: {', '.join(m['name'] for m in models)}."

    if variant_name:
        variant = vehicle_db.get_variant_details(model_name, variant_name)
        if variant:
            return json.dumps({"model": summary["model_name"], "variant": variant}, indent=2)

    return json.dumps(summary, indent=2)


@tool
async def create_lead_record(
    full_name: Annotated[
        str,
        "Customer's full legal name (first and last name, e.g., 'Vikram Rao').",
    ],
    phone: Annotated[
        str,
        "Customer's 10-digit primary mobile contact number (e.g., '9820123456').",
    ],
    email: Annotated[
        str,
        "Customer's valid email address for booking and dealership follow-up correspondence.",
    ],
    city: Annotated[
        str,
        "Customer's preferred city or location for dealership test drive (e.g., 'Mumbai', 'Pune', 'Delhi').",
    ],
    model_of_interest: Annotated[
        Literal["XUV700", "Thar", "Scorpio-N", "Bolero Neo"],
        "The specific Mahindra vehicle model the customer wishes to test drive or purchase.",
    ],
    company: Annotated[
        Optional[str],
        "Customer's company or buyer profile (e.g., 'Retail Customer', 'Corporate Fleet').",
    ] = "Retail Customer",
    lead_source: Annotated[
        Literal["Mahindra AI Digital Showroom", "Web Chat", "WhatsApp", "Dealership Walk-in"],
        "Marketing or engagement channel origin of the prospective lead.",
    ] = "Mahindra AI Digital Showroom",
    lead_status: Annotated[
        Literal["New", "Contacted", "Attempted to Contact"],
        "Current lifecycle status of the prospective lead.",
    ] = "New",
) -> str:
    """Creates a new prospect Lead in Zoho CRM once all slots are gathered.
    
    Args:
        full_name: Customer's full name.
        phone: 10-digit mobile number.
        email: Valid email address.
        city: Customer's city/location.
        model_of_interest: Mahindra vehicle model.
        company: Customer's company or buyer type.
        lead_source: Channel origin of the lead.
        lead_status: Current lifecycle status of the lead.
    """
    parts = full_name.strip().split(" ", 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else "Customer"

    payload = {
        "First_Name": first_name,
        "Last_Name": last_name,
        "Phone": phone,
        "Email": email,
        "City": city,
        "Company": company or "Retail Customer",
        "Lead_Source": lead_source or "Mahindra AI Digital Showroom",
        "Lead_Status": lead_status or "New",
        "Vehicle_Model_of_Interest": model_of_interest,
        "Description": f"Test drive requested for Mahindra {model_of_interest}. Location: {city}. Sourced via AI Digital Concierge.",
    }
    result = await zoho_service.create_lead(payload)
    return json.dumps(result)


@tool
async def lookup_deal_status(
    identifier: Annotated[
        str,
        "Prospect's registered 10-digit phone number (e.g., '9819988776') or Zoho Deal ID (e.g., 'DEAL-2001').",
    ],
) -> str:
    """Searches active Deal records in Zoho CRM using phone number or Deal ID.
    
    Args:
        identifier: Prospect's phone number or Zoho Deal ID (e.g., 'DEAL-2001' or '9819988776').
    """
    deal = await zoho_service.search_deal(identifier)
    if not deal:
        return f"No active test drive or quote record found for '{identifier}'. Please check the details or provide your registered phone number."
    return json.dumps(deal, indent=2)


@tool
async def update_deal_status(
    deal_id: Annotated[
        str,
        "Zoho Deal ID of the active test drive or quotation record to update (e.g., 'DEAL-2001').",
    ],
    follow_up_preference: Annotated[
        str,
        "Updated customer communication preference, timing, or channel (e.g., 'WhatsApp confirmation requested', 'Call on Saturday afternoon').",
    ],
) -> str:
    """Updates follow-up preferences or rescheduled timing for an active deal in Zoho CRM.
    
    Args:
        deal_id: Zoho Deal ID.
        follow_up_preference: Updated customer notes or schedule preference.
    """
    result = await zoho_service.update_deal(deal_id, {"Follow_Up_Preference": follow_up_preference})
    return json.dumps(result)


@tool
async def check_booking_status(
    booking_id_or_phone: Annotated[
        str,
        "Customer's Booking Reference ID (format #MAH-XXXX, e.g., 'MAH-9921') or registered 10-digit phone number.",
    ],
) -> str:
    """Fetches booking stage, VIN allocation, and delivery schedule from Zoho CRM.
    
    Args:
        booking_id_or_phone: Booking ID (e.g. 'MAH-9921') or customer phone number.
    """
    deal = await zoho_service.get_booking(booking_id_or_phone)
    if not deal:
        return f"No booking record found for '{booking_id_or_phone}'. Please confirm your Booking Reference ID (format #MAH-XXXX) or registered phone number."
    return json.dumps(deal, indent=2)


@tool
async def log_service_ticket(
    contact_name: Annotated[
        str,
        "Vehicle owner or primary contact person's full name.",
    ],
    phone: Annotated[
        str,
        "Owner's 10-digit primary mobile contact number.",
    ],
    registration_number: Annotated[
        str,
        "Vehicle license plate registration number (e.g., 'MH01AB1234', 'DL2CA9999').",
    ],
    odometer: Annotated[
        str,
        "Current vehicle odometer reading in kilometers (e.g., '20000').",
    ],
    issue_type: Annotated[
        str,
        "Description of problem, symptom, or scheduled maintenance milestone (e.g., 'Brake vibration & shudder', '20,000 km Periodic Service').",
    ],
    preferred_center: Annotated[
        Literal[
            "Worli", "Andheri", "Thane", "Kandivali", "Kurla", "Navi Mumbai",
            "Bandra", "Goregaon", "Borivali", "Dadar", "Chembur"
        ],
        "Preferred authorized Mahindra dealership service workshop location.",
    ],
    priority: Annotated[
        Literal["High", "Medium", "Low"],
        "Assessed urgency/severity: 'High' for safety hazards, brake failure, engine overheating, or vehicle breakdown; 'Medium' for operational defects, AC failure, abnormal noises, or warning lights; 'Low' for routine maintenance, oil changes, or periodic inspection.",
    ] = "Medium",
    status: Annotated[
        Literal["New", "Service Appointment Scheduled", "Escalated"],
        "Initial ticket state: 'Service Appointment Scheduled' when workshop center and issue are established; 'Escalated' for emergencies/breakdowns; 'New' for general unassigned requests.",
    ] = "Service Appointment Scheduled",
    case_origin: Annotated[
        Literal["Chat", "Web", "Phone", "WhatsApp"],
        "Intake communication channel where customer initiated the request.",
    ] = "Chat",
    case_type: Annotated[
        Optional[Literal["Periodic Maintenance", "Complaint"]],
        "Classification of the ticket: 'Periodic Maintenance' for routine scheduled service, 'Complaint' for mechanical or electrical defects.",
    ] = None,
    related_deal_id: Annotated[
        Optional[str],
        "Zoho Deal record ID to populate 'Related To' lookup field on the Case.",
    ] = None,
    contact_id: Annotated[
        Optional[str],
        "Zoho Contact record ID to populate 'Contact Name' lookup field on the Case.",
    ] = None,
    account_id: Annotated[
        Optional[str],
        "Zoho Account record ID to populate 'Account Name' lookup field on the Case.",
    ] = None,
) -> str:
    """Logs a maintenance booking or service complaint in the Zoho Cases module.
    
    Args:
        contact_name: Vehicle owner's name.
        phone: Owner's phone number.
        registration_number: Vehicle license plate (e.g. 'MH01AB1234').
        odometer: Current vehicle kilometer reading.
        issue_type: Description of problem or scheduled maintenance milestone.
        preferred_center: Dealership service workshop location.
        priority: Assessed severity ('High', 'Medium', 'Low').
        status: Ticket lifecycle status.
        case_origin: Communication channel.
        case_type: Category of service case.
        related_deal_id: Associated Deal ID for 'Related To' lookup.
        contact_id: Associated Contact ID for 'Contact Name' lookup.
        account_id: Associated Account ID for 'Account Name' lookup.
    """
    resolved_type = case_type or ("Periodic Maintenance" if "service" in issue_type.lower() else "Complaint")
    payload = {
        "Subject": f"Service Request: {registration_number.upper()} - {issue_type}",
        "Phone": phone,
        "Registration_Number": registration_number.upper(),
        "Odometer_Reading": str(odometer),
        "Issue_Type": issue_type,
        "Preferred_Center": preferred_center,
        "Priority": priority,
        "Status": status,
        "Case_Origin": case_origin,
        "Type": resolved_type,
        "Description": f"Vehicle Registration: {registration_number.upper()} | Odometer: {odometer} km | Service Requirement: {issue_type} | Authorized Center: {preferred_center} | Logged via AI Concierge",
    }

    if contact_id:
        payload["Contact_Name"] = {"id": contact_id}
    elif contact_name:
        payload["Contact_Name_Text"] = contact_name

    if related_deal_id:
        payload["Related_To"] = {"id": related_deal_id}

    if account_id:
        payload["Account_Name"] = {"id": account_id}

    result = await zoho_service.create_service_case(payload)
    return json.dumps(result)
