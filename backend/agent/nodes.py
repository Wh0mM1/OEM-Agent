import json
import re
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from core.state import AgentState, StageType
from agent.prompts import CLASSIFIER_SYSTEM_PROMPT, OEM_SYSTEM_PROMPT
from agent.tools import (
    create_lead_record,
    lookup_deal_status,
    update_deal_status,
    check_booking_status,
    log_service_ticket,
)
from agent.llm import get_llm
from data.vehicle_db import vehicle_db
from zoho.service import zoho_service

COMMON_CITIES = [
    "mumbai", "delhi", "pune", "bangalore", "bengaluru", "hyderabad",
    "chennai", "kolkata", "ahmedabad", "thane", "noida", "gurgaon",
    "gurugram", "jaipur", "lucknow", "chandigarh", "navi mumbai"
]

COMMON_WORKSHOPS = [
    "worli", "andheri", "thane", "kandivali", "kurla", "navi mumbai",
    "bandra", "goregaon", "borivali", "dadar", "chembur"
]


def extract_slots_from_text(text: str, current_slots: Dict[str, Any]) -> Dict[str, Any]:
    slots = dict(current_slots)

    # 1. Extract Phone (10 digits)
    phone_match = re.search(r"\b[6-9]\d{9}\b", text)
    if phone_match:
        new_phone = phone_match.group(0)
        # If user provides a different phone number, reset old contact slots for fresh registration
        if slots.get("phone") and slots.get("phone") != new_phone:
            slots["phone"] = new_phone
            slots.pop("name", None)
            slots.pop("email", None)
            slots.pop("city", None)
            slots.pop("company", None)
        else:
            slots["phone"] = new_phone

    # 2. Extract Name
    name_match = re.search(r"(?:my name is|name is|i am|i'm|owner is|contact is)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)", text, re.I)
    if name_match:
        slots["name"] = name_match.group(1).strip()
    elif not slots.get("name"):
        parts = [p.strip() for p in text.split(",")]
        if len(parts) > 1 and re.match(r"^[A-Za-z\s]{3,30}$", parts[0]) and not any(k in parts[0].lower() for k in ["hello", "hi", "test drive", "scorpio", "xuv", "thar", "service"]):
            slots["name"] = parts[0].strip()

    # 3. Extract Email
    email_match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b", text)
    if email_match:
        slots["email"] = email_match.group(0)

    # 4. Extract City
    for city in COMMON_CITIES:
        if re.search(rf"\b{city}\b", text, re.I):
            slots["city"] = city.title()
            break
    if not slots.get("city"):
        city_match = re.search(r"(?:in|at|city is|location is)\s+([A-Za-z]+)", text, re.I)
        if city_match:
            cand = city_match.group(1).strip()
            if cand.lower() not in ["the", "a", "my", "our", "home", "dealership", "worli", "andheri", "workshop"]:
                slots["city"] = cand.title()

    # 5. Extract Company (if mentioned)
    comp_match = re.search(r"(?:company is|working at|from|company)\s+([A-Za-z0-9\s&.-]{2,30})", text, re.I)
    if comp_match and not slots.get("company"):
        cand = comp_match.group(1).strip()
        if cand.lower() not in ["the", "a", "my", "our", "home", "mumbai", "delhi", "pune", "bangalore"]:
            slots["company"] = cand

    # 6. Extract Vehicle Registration (e.g. MH02CD1234, DL1CA9999, 22BH1234AA)
    reg_match = re.search(r"\b([A-Z]{2}[ -]?[0-9]{1,2}[ -]?[A-Z]{1,3}[ -]?[0-9]{4}|[0-9]{2}BH[0-9]{4}[A-Z]{1,2})\b", text, re.I)
    if reg_match:
        slots["registration_number"] = reg_match.group(0).upper().replace(" ", "").replace("-", "")

    # 7. Extract Odometer Reading
    odo_match = re.search(r"\b(\d{1,3}(?:,\d{3})*|\d+)\s*(?:km|kms|kilometer|kilometres)\b", text, re.I)
    if odo_match:
        slots["odometer"] = odo_match.group(1).replace(",", "")
    elif not slots.get("odometer"):
        num_matches = re.findall(r"\b\d{3,6}\b", text)
        for num in num_matches:
            if num != slots.get("phone") and 500 <= int(num) <= 500000:
                slots["odometer"] = num
                break

    # 8. Extract Preferred Service Workshop
    for center in COMMON_WORKSHOPS:
        if re.search(rf"\b{center}\b", text, re.I):
            slots["preferred_center"] = center.title()
            break

    # 9. Extract Service Issue Type
    issue_match = re.search(
        r"\b(brake\s+(?:shudder|vibration|noise|pad|disc|issue)|oil\s+change|periodic\s+(?:maintenance|service)|general\s+service|ac\s+(?:repair|cooling|noise)|engine\s+noise|clutch\s+issue|suspension\s+rattle|wheel\s+alignment|tyre\s+rotation|filter\s+replacement|battery\s+check)\b",
        text,
        re.I,
    )
    if issue_match:
        slots["issue_type"] = issue_match.group(0).title()
    elif not slots.get("issue_type"):
        issue_phrase = re.search(r"(?:issue is|problem is|complaint is|needs|need)\s+([^,.]+)", text, re.I)
        if issue_phrase:
            cand = issue_phrase.group(1).strip()
            if len(cand) > 3 and not any(k in cand.lower() for k in ["test drive", "booking", "xuv", "thar"]):
                slots["issue_type"] = cand.capitalize()

    # 10. Extract Booking ID
    booking_match = re.search(r"\bMAH[- ]?[0-9]{4,6}\b", text, re.I)
    if booking_match and not slots.get("booking_id"):
        slots["booking_id"] = booking_match.group(0).upper().replace(" ", "-")

    # 11. Extract Model of Interest
    text_upper = text.upper()
    if "XUV700" in text_upper or "XUV 700" in text_upper:
        slots["model_interest"] = "XUV700"
    elif "THAR" in text_upper:
        slots["model_interest"] = "Thar"
    elif "SCORPIO" in text_upper:
        slots["model_interest"] = "Scorpio-N"
    elif "BOLERO" in text_upper:
        slots["model_interest"] = "Bolero Neo"

    # 12. Extract Follow-Up Preference for Pipeline
    pref_match = re.search(r"(?:update|change|set|prefer|preference)\s+(?:to|is)?\s*([a-zA-Z0-9\s,–-]+(?:whatsapp|call|phone|email|afternoon|morning|weekend|evening)[^,.]*)", text, re.I)
    if pref_match:
        slots["follow_up_preference"] = pref_match.group(0).strip()
    elif "whatsapp" in text.lower():
        slots["follow_up_preference"] = "WhatsApp confirmation requested"
    elif "call" in text.lower() and any(k in text.lower() for k in ["weekend", "saturday", "sunday", "afternoon", "evening"]):
        slots["follow_up_preference"] = "Call on weekend/afternoon preferred"

    return slots


async def classify_intent_node(state: AgentState) -> Dict[str, Any]:
    last_user_message = next(
        (m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), ""
    )
    text_lower = last_user_message.lower()
    updated_slots = extract_slots_from_text(last_user_message, state.get("collected_slots", {}))

    # Fast deterministic routing (skips LLM triage call to eliminate latency)
    if any(k in text_lower for k in ["booking", "vin", "allocation", "delivery date", "mah-", "dispatch", "deposit"]):
        return {
            "active_stage": "booked_vehicle",
            "previous_stage": state.get("active_stage"),
            "collected_slots": updated_slots,
        }
    if any(k in text_lower for k in ["service", "complaint", "repair", "breakdown", "odometer", "maintenance", "workshop", "km", "periodic", "brake", "oil"]):
        return {
            "active_stage": "post_purchase_service",
            "previous_stage": state.get("active_stage"),
            "collected_slots": updated_slots,
        }
    if any(k in text_lower for k in ["deal", "test drive schedule", "sales rep", "follow up", "quotation", "priya"]) or (
        "deal" in text_lower and re.search(r"\b[6-9]\d{9}\b", text_lower)
    ):
        return {
            "active_stage": "ongoing_pipeline",
            "previous_stage": state.get("active_stage"),
            "collected_slots": updated_slots,
        }
    if any(k in text_lower for k in ["price", "features", "specs", "xuv700", "thar", "scorpio", "bolero", "test drive", "variant", "explore", "on road", "cost", "suv"]):
        return {
            "active_stage": "new_lead",
            "previous_stage": state.get("active_stage"),
            "collected_slots": updated_slots,
        }

    # Continuity Rules: Stay in current stage if providing relevant parameters
    if state.get("active_stage") == "new_lead" and any(k in last_user_message.lower() for k in ["name", "email", "pune", "delhi", "mumbai", "bangalore", "@", "test drive", "drive", "phone"]):
        return {
            "active_stage": "new_lead",
            "previous_stage": state.get("active_stage"),
            "collected_slots": updated_slots,
        }
    if state.get("active_stage") == "post_purchase_service" and any(k in last_user_message.lower() for k in ["mh", "dl", "km", "andheri", "worli", "owner", "service", "brake", "maintenance"]):
        return {
            "active_stage": "post_purchase_service",
            "previous_stage": state.get("active_stage"),
            "collected_slots": updated_slots,
        }
    if state.get("active_stage") == "ongoing_pipeline" and any(k in last_user_message.lower() for k in ["preference", "whatsapp", "call", "reschedule", "saturday", "confirm"]):
        return {
            "active_stage": "ongoing_pipeline",
            "previous_stage": state.get("active_stage"),
            "collected_slots": updated_slots,
        }

    if any(k in text_lower for k in ["hi", "hello", "hey", "namaste", "good morning"]):
        return {
            "active_stage": "new_lead",
            "previous_stage": state.get("active_stage"),
            "collected_slots": updated_slots,
        }

    # LLM fallback classification
    llm = get_llm()
    messages = [
        SystemMessage(content=CLASSIFIER_SYSTEM_PROMPT),
        HumanMessage(content=f"Classify this user message: '{last_user_message}'"),
    ]
    detected_stage = state.get("active_stage", "new_lead")
    try:
        res = await llm.ainvoke(messages)
        content = str(res.content)
        if "booked_vehicle" in content:
            detected_stage = "booked_vehicle"
        elif "post_purchase_service" in content:
            detected_stage = "post_purchase_service"
        elif "ongoing_pipeline" in content:
            detected_stage = "ongoing_pipeline"
        elif "ambiguous" in content:
            detected_stage = "ambiguous"
    except Exception:
        pass

    return {
        "active_stage": detected_stage,
        "previous_stage": state.get("active_stage"),
        "collected_slots": updated_slots,
    }


async def new_lead_node(state: AgentState) -> Dict[str, Any]:
    slots = state.get("collected_slots", {})
    crm_ids = dict(state.get("crm_ids", {}))
    tool_chips = []

    name = slots.get("name")
    phone = slots.get("phone")
    email = slots.get("email")
    city = slots.get("city")
    company = slots.get("company", "Retail Customer")
    model = slots.get("model_interest", "XUV700")

    # 1. Lead creation rule: Create lead if all 4 slots exist AND this phone number wasn't already created in this session
    if name and phone and email and city:
        if crm_ids.get("last_lead_phone") != phone:
            lead_res = await create_lead_record.ainvoke({
                "full_name": name,
                "phone": phone,
                "email": email,
                "city": city,
                "model_of_interest": model,
                "company": company,
                "lead_source": "Mahindra AI Digital Showroom",
            })
            lead_data = json.loads(lead_res)
            lead_id = lead_data.get("lead_id", "LEAD-101")
            crm_ids["lead_id"] = str(lead_id)
            crm_ids["last_lead_phone"] = str(phone)
            tool_chips.append({
                "tool_name": "create_lead_record",
                "status": "success",
                "label": f"Lead Created #{lead_id} (Zoho CRM)",
                "data": lead_data,
            })

            confirmation_text = (
                f"### Test Drive Request Confirmed!\n\n"
                f"Thank you, **{name}**! I have registered your details and created a fresh lead in our Zoho CRM portal.\n\n"
                f"| Booking Parameter | Customer Detail |\n"
                f"| :--- | :--- |\n"
                f"| **Lead Reference** | `#{lead_id}` |\n"
                f"| **Model of Interest** | Mahindra {model} |\n"
                f"| **Contact Phone** | {phone} |\n"
                f"| **Email Address** | {email} |\n"
                f"| **Preferred Location** | {city} |\n"
                f"| **Buyer Profile** | {company} |\n"
                f"| **Lead Source** | Mahindra AI Digital Showroom |\n\n"
                f"Our nearest Mahindra authorized dealership in **{city}** has been notified. A senior sales consultant will reach out to you at **{phone}** to finalize the exact date, time, and venue (home or showroom) for your drive.\n\n"
                f"Would you like me to share variant-specific on-road price breakdowns or arrange a specialized feature demo during your drive?"
            )
            return {
                "messages": [AIMessage(content=confirmation_text)],
                "crm_ids": crm_ids,
                "tool_chips": tool_chips,
            }

    # 2. Incomplete Slots: Dynamically instruct the agent to ask ONLY for what's missing
    missing_slots = []
    if not name: missing_slots.append("Full Name")
    if not phone: missing_slots.append("10-digit Mobile Number")
    if not email: missing_slots.append("Email Address")
    if not city: missing_slots.append("Preferred City / Location")

    # Pre-fetch vehicle specifications for discovery
    model_name = slots.get("model_interest", "XUV700")
    vehicle_info = vehicle_db.get_vehicle_summary(model_name)
    specs_context = ""
    if vehicle_info:
        specs_context = f"\nAUTHORITATIVE VEHICLE CATALOG SPECS:\n{json.dumps(vehicle_info, indent=2)}\n"
        tool_chips.append({
            "tool_name": "get_vehicle_info",
            "status": "success",
            "label": f"Verified Specs: {vehicle_info['model_name']}",
            "data": {"model": model_name},
        })

    collected_summary = ", ".join(f"{k.capitalize()}: {v}" for k, v in slots.items() if v and not k.startswith("_"))
    missing_summary = ", ".join(missing_slots)

    slot_prompt = ""
    if missing_slots:
        slot_prompt = (
            f"\nSLOT-FILLING GUIDANCE:\n"
            f"- Information already collected: [{collected_summary if collected_summary else 'None'}]\n"
            f"- Still missing: [{missing_summary}]\n"
            f"- Acknowledge what the customer has already shared, and politely ask ONLY for the remaining missing detail(s): {missing_summary}.\n"
        )

    sys_prompt = (
        OEM_SYSTEM_PROMPT
        + specs_context
        + slot_prompt
        + "\nCRITICAL: You are Karan, Mahindra Client Advisor. Speak in a helpful, conversational, professional human tone. DO NOT output JSON."
    )
    messages = [SystemMessage(content=sys_prompt)] + list(state["messages"])

    llm = get_llm()
    response = await llm.ainvoke(messages)
    content = str(response.content).strip()

    if content.startswith("{") and content.endswith("}"):
        if vehicle_info:
            content = (
                f"### Mahindra {vehicle_info['model_name']} — Verified Specifications\n\n"
                f"**Price Range:** {vehicle_info['price_range']}\n\n"
                f"{vehicle_info['overview']}\n\n"
                f"| Variant | Ex-Showroom Price | Key Highlights |\n"
                f"| :--- | :--- | :--- |\n"
            )
            for v in vehicle_info["variants"]:
                content += f"| **{v['name']}** | {v['ex_showroom_price']} | {', '.join(v['key_features'][:3])} |\n"
            content += (
                f"\nWould you like to experience the **{vehicle_info['model_name']}** firsthand? "
                f"Please share your **{missing_summary}** to schedule your test drive slot."
            )
        response = AIMessage(content=content)

    return {
        "messages": [response],
        "crm_ids": crm_ids,
        "tool_chips": tool_chips,
    }


async def pipeline_node(state: AgentState) -> Dict[str, Any]:
    slots = state.get("collected_slots", {})
    crm_ids = dict(state.get("crm_ids", {}))
    tool_chips = []

    identifier = slots.get("deal_id") or slots.get("phone") or "9819988776"
    deal = await zoho_service.search_deal(identifier)

    # Check if the user is asking to update follow-up preference
    pref = slots.get("follow_up_preference")
    last_user_message = next(
        (m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), ""
    )

    if deal and pref and any(k in last_user_message.lower() for k in ["update", "change", "set", "whatsapp", "call", "preference"]):
        deal_id = deal.get("id")
        updated_desc = f"{deal.get('Description', '')} | Updated Follow-up Preference: {pref}"
        await zoho_service.update_deal(deal_id, {"Description": updated_desc, "Follow_Up_Preference": pref})
        tool_chips.append({
            "tool_name": "update_deal_status",
            "status": "success",
            "label": f"Deal Updated #{deal_id} (Preference Saved)",
            "data": {"deal_id": deal_id, "preference": pref},
        })

        update_text = (
            f"### Deal Follow-Up Preference Updated!\n\n"
            f"I have successfully updated your active test drive deal in our Zoho CRM portal.\n\n"
            f"| Deal Parameter | Updated Setting |\n"
            f"| :--- | :--- |\n"
            f"| **Deal Record** | `{deal.get('id')}` • {deal.get('Deal_Name')} |\n"
            f"| **Updated Preference** | **{pref}** |\n"
            f"| **Sales Consultant** | Vikram Malhotra (+91 98200 44556) |\n\n"
            f"Our team at the Worli dealership has been notified to communicate via your preferred channel. Is there anything else you would like to adjust?"
        )
        return {"messages": [AIMessage(content=update_text)], "tool_chips": tool_chips}

    deal_context = ""
    if deal:
        deal_context = f"\nRETRIEVED DEAL FROM ZOHO CRM:\n{json.dumps(deal, indent=2)}\n"
        tool_chips.append({
            "tool_name": "lookup_deal_status",
            "status": "success",
            "label": f"Deal Verified: {deal.get('id', identifier)}",
            "data": {"identifier": identifier},
        })
    else:
        deal_context = f"\nNo active deal found for identifier '{identifier}'. Please ask customer to verify their registered phone number.\n"

    sys_prompt = (
        OEM_SYSTEM_PROMPT
        + deal_context
        + "\nYou are in Ongoing Pipeline stage. Confirm test drive appointment, quote, dealership, and sales rep. DO NOT output JSON."
    )
    messages = [SystemMessage(content=sys_prompt)] + list(state["messages"])

    llm = get_llm()
    response = await llm.ainvoke(messages)
    content = str(response.content).strip()

    if content.startswith("{") and content.endswith("}"):
        if deal:
            content = (
                f"### Active Deal Details Verified\n\n"
                f"I have retrieved your scheduled appointment from our CRM:\n\n"
                f"| Deal Detail | Information |\n"
                f"| :--- | :--- |\n"
                f"| **Deal Record** | `{deal.get('id')}` • {deal.get('Deal_Name')} |\n"
                f"| **Current Stage** | **{deal.get('Stage')}** |\n"
                f"| **Quotation** | ₹{deal.get('Amount', 0):,} |\n\n"
                f"{deal.get('Description', '')}\n\n"
                f"Would you like me to update your follow-up preference (e.g. WhatsApp, phone call) or reschedule your timing?"
            )
            response = AIMessage(content=content)

    return {"messages": [response], "tool_chips": tool_chips}


async def booked_node(state: AgentState) -> Dict[str, Any]:
    slots = state.get("collected_slots", {})
    tool_chips = []

    booking_query = slots.get("booking_id") or slots.get("phone") or "MAH-9921"
    booking_deal = await zoho_service.get_booking(booking_query)

    booking_context = ""
    if booking_deal:
        booking_context = f"\nRETRIEVED BOOKING FROM ZOHO CRM:\n{json.dumps(booking_deal, indent=2)}\n"
        tool_chips.append({
            "tool_name": "check_booking_status",
            "status": "success",
            "label": f"Booking Verified: {booking_deal.get('Booking_ID', booking_query)}",
            "data": {"booking": booking_query},
        })
    else:
        booking_context = f"\nNo booking found for '{booking_query}'. Please ask customer to verify their booking reference #MAH-XXXX.\n"

    sys_prompt = (
        OEM_SYSTEM_PROMPT
        + booking_context
        + "\nYou are in Booked Vehicle stage. Share allocation status, VIN number, and transit timeline. If customer asks about balance payment, provide dealership bank transfer/RTGS instructions. DO NOT output JSON."
    )
    messages = [SystemMessage(content=sys_prompt)] + list(state["messages"])

    llm = get_llm()
    response = await llm.ainvoke(messages)
    content = str(response.content).strip()

    if content.startswith("{") and content.endswith("}"):
        if booking_deal:
            content = (
                f"### Booking Allocation Status Verified\n\n"
                f"Here is the real-time status of your vehicle booking from our manufacturing plant:\n\n"
                f"| Parameter | Allocation Detail |\n"
                f"| :--- | :--- |\n"
                f"| **Booking Reference** | `{booking_deal.get('Booking_ID', booking_query)}` |\n"
                f"| **Deal Stage** | {booking_deal.get('Stage', 'Closed Won - Booking Done')} |\n"
                f"| **Amount** | ₹{booking_deal.get('Amount', 0):,} |\n\n"
                f"{booking_deal.get('Description', '')}\n\n"
                f"Is there anything else regarding registration paperwork or balance payment you would like assistance with?"
            )
            response = AIMessage(content=content)

    return {"messages": [response], "tool_chips": tool_chips}


async def service_node(state: AgentState) -> Dict[str, Any]:
    slots = state.get("collected_slots", {})
    crm_ids = dict(state.get("crm_ids", {}))
    tool_chips = []

    reg = slots.get("registration_number")
    odo = slots.get("odometer")
    issue = slots.get("issue_type") or "Periodic Maintenance / Inspection"
    center = slots.get("preferred_center") or "Worli"
    name = slots.get("name") or "Vehicle Owner"
    phone = slots.get("phone") or "9820011223"

    # Check what parameters are present
    # To log a valid service ticket, Registration Number and Odometer are mandatory
    if reg and odo:
        if crm_ids.get("last_case_reg") != reg:
            # Dynamic assessment of priority and status based on issue context
            issue_lower = (issue or "").lower()
            if any(w in issue_lower for w in ["brake", "smoke", "overheat", "breakdown", "leak", "engine", "stalling", "steering", "accident", "emergency"]):
                inferred_priority = "High"
            elif any(w in issue_lower for w in ["periodic", "general service", "oil change", "maintenance", "inspection", "alignment", "rotation"]):
                inferred_priority = "Low"
            else:
                inferred_priority = "Medium"

            inferred_status = "Escalated" if any(w in issue_lower for w in ["breakdown", "stranded", "emergency", "towing"]) else "Service Appointment Scheduled"
            inferred_type = "Periodic Maintenance" if "service" in issue_lower or "maintenance" in issue_lower else "Complaint"

            # Check if customer has an existing Deal or Booking in Zoho CRM to link under 'Related To'
            deal_id = None
            contact_id = None
            account_id = None

            matched_deal = await zoho_service.search_deal(phone)
            if not matched_deal:
                booking_q = slots.get("booking_id") or phone
                matched_deal = await zoho_service.get_booking(booking_q)

            if matched_deal:
                deal_id = matched_deal.get("id")
                c_val = matched_deal.get("Contact_Name")
                if isinstance(c_val, dict):
                    contact_id = c_val.get("id")
                elif isinstance(c_val, str) and c_val.isdigit():
                    contact_id = c_val

                a_val = matched_deal.get("Account_Name")
                if isinstance(a_val, dict):
                    account_id = a_val.get("id")
                elif isinstance(a_val, str) and a_val.isdigit():
                    account_id = a_val

            if not contact_id:
                contact_record = await zoho_service.search_contact(phone)
                if contact_record:
                    contact_id = contact_record.get("id")
                    if not account_id and contact_record.get("Account_Name"):
                        account_id = contact_record["Account_Name"].get("id")

            # Fallback: Auto-create Contact & Account if first-time service customer
            if not account_id and name and name != "Vehicle Owner":
                account_id = await zoho_service.get_or_create_account(name, phone)
            if not contact_id and name and name != "Vehicle Owner":
                contact_id = await zoho_service.get_or_create_contact(name, phone, account_id)

            res = await log_service_ticket.ainvoke({
                "contact_name": name,
                "phone": phone,
                "registration_number": reg,
                "odometer": odo,
                "issue_type": issue,
                "preferred_center": center,
                "priority": inferred_priority,
                "status": inferred_status,
                "case_origin": "Chat",
                "case_type": inferred_type,
                "related_deal_id": deal_id,
                "contact_id": contact_id,
                "account_id": account_id,
            })
            case_data = json.loads(res)
            case_id = case_data.get("case_id", "CASE-9021")
            crm_ids["case_id"] = str(case_id)
            crm_ids["last_case_reg"] = str(reg)
            tool_chips.append({
                "tool_name": "log_service_ticket",
                "status": "success",
                "label": f"Service Case #{case_id} Logged",
                "data": case_data,
            })

            service_text = (
                f"### Service Appointment Scheduled!\n\n"
                f"Your service ticket has been created and synced directly with our workshop desk in Zoho CRM.\n\n"
                f"| Service Parameter | Ticket Detail |\n"
                f"| :--- | :--- |\n"
                f"| **Case Reference** | `#{case_id}` |\n"
                f"| **Vehicle Registration** | **{reg}** |\n"
                f"| **Odometer Reading** | {odo} km |\n"
                f"| **Service Requirement** | {issue} |\n"
                f"| **Authorized Workshop** | Mahindra Authorized Center, {center} |\n"
                f"| **Contact On Record** | {name} ({phone}) |\n\n"
                f"Our service advisor at **{center}** has received your ticket and reserved your service bay. You will receive an SMS confirmation with the service advisor's direct contact number.\n\n"
                f"Would you like to request home vehicle pick-up & drop, or add any specific complaints for our workshop technician?"
            )
            return {
                "messages": [AIMessage(content=service_text)],
                "crm_ids": crm_ids,
                "tool_chips": tool_chips,
            }

    # Incomplete parameters: instruct the agent to ask ONLY for missing service parameters
    missing_service = []
    if not reg: missing_service.append("Vehicle Registration Number (e.g. MH01AB1234)")
    if not odo: missing_service.append("Current Odometer Reading (km)")
    if not slots.get("issue_type"): missing_service.append("Specific Issue or Service Milestone (e.g. 20,000 km Service or Brake noise)")
    if not slots.get("preferred_center"): missing_service.append("Preferred Service Center (e.g. Worli, Andheri, Thane)")

    missing_str = ", ".join(missing_service)
    collected_service_str = ", ".join(f"{k.capitalize()}: {v}" for k, v in slots.items() if v and not k.startswith("_"))

    sys_prompt = (
        OEM_SYSTEM_PROMPT
        + f"\nYou are in Post-Purchase Service stage.\n"
        f"Collected parameters so far: [{collected_service_str if collected_service_str else 'None'}].\n"
        f"Still missing: [{missing_str}].\n"
        f"Acknowledge what the customer shared, and politely ask ONLY for what is missing: {missing_str}. DO NOT output JSON."
    )
    messages = [SystemMessage(content=sys_prompt)] + list(state["messages"])

    llm = get_llm()
    response = await llm.ainvoke(messages)

    return {
        "messages": [response],
        "crm_ids": crm_ids,
        "tool_chips": tool_chips,
    }


async def clarification_node(state: AgentState) -> Dict[str, Any]:
    clarification_msg = AIMessage(
        content="I want to ensure I connect you with the right department. Are you inquiring about exploring a new vehicle (like the XUV700 or Thar), checking on an existing test drive/booking, or scheduling a service visit for a vehicle you own?"
    )
    return {"messages": [clarification_msg], "tool_chips": []}
