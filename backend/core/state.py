from typing import Annotated, Dict, Any, List, Optional, Literal
from typing_extensions import TypedDict
import operator
from langchain_core.messages import AnyMessage

StageType = Literal[
    "new_lead",
    "ongoing_pipeline",
    "booked_vehicle",
    "post_purchase_service",
    "ambiguous",
]


class SlotStore(TypedDict, total=False):
    # New Lead Slots
    name: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    city: Optional[str]
    model_interest: Optional[str]

    # Service Slots
    registration_number: Optional[str]
    odometer: Optional[str]
    issue_type: Optional[str]
    preferred_center: Optional[str]

    # Pipeline & Booking Lookups
    deal_id: Optional[str]
    booking_id: Optional[str]


class ToolExecutionChip(TypedDict):
    tool_name: str
    status: Literal["pending", "success", "error"]
    label: str
    data: Optional[Dict[str, Any]]


class AgentState(TypedDict):
    messages: Annotated[List[AnyMessage], operator.add]
    session_id: str
    thread_id: str
    active_stage: StageType
    previous_stage: Optional[StageType]
    collected_slots: Dict[str, Any]
    crm_ids: Dict[str, str]  # e.g., {"lead_id": "...", "deal_id": "...", "case_id": "..."}
    tool_chips: Annotated[List[ToolExecutionChip], operator.add]
    clarification_prompt: Optional[str]
    error_message: Optional[str]
    custom_llm_key: Optional[str]
    custom_llm_model: Optional[str]
