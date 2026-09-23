from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    thread_id: Optional[str] = None
    openrouter_key: Optional[str] = None
    openrouter_model: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    thread_id: str
    active_stage: str
    response: str
    tool_chips: List[Dict[str, Any]] = Field(default_factory=list)
    collected_slots: Dict[str, Any] = Field(default_factory=dict)
    crm_ids: Dict[str, str] = Field(default_factory=dict)
    requires_custom_key: bool = False
    rate_limit_info: Optional[Dict[str, Any]] = None


class VehicleVariant(BaseModel):
    name: str
    ex_showroom_price: str
    transmission: str
    seating: int
    fuel_type: str
    key_features: List[str]


class VehicleModel(BaseModel):
    model_name: str
    tagline: str
    segment: str
    price_range: str
    variants: List[VehicleVariant]
    overview: str


class LeadCreatePayload(BaseModel):
    first_name: str = Field(description="First name of the prospective customer.")
    last_name: str = Field(default="Customer", description="Last name of the prospective customer.")
    phone: str = Field(description="10-digit primary mobile contact number.")
    email: str = Field(description="Valid email address for communications.")
    city: str = Field(description="Customer's preferred city or location for test drive.")
    model_of_interest: Literal["XUV700", "Thar", "Scorpio-N", "Bolero Neo"] = Field(
        description="The Mahindra vehicle model of interest."
    )
    company: Optional[str] = Field(
        default="Retail Customer",
        description="Customer company name or profile type.",
    )
    lead_source: Literal["Mahindra AI Digital Showroom", "Web Chat", "WhatsApp", "Dealership Walk-in"] = Field(
        default="Mahindra AI Digital Showroom",
        description="Origin channel of the lead.",
    )


class ServiceCasePayload(BaseModel):
    contact_name: str = Field(description="Vehicle owner or primary contact person's name.")
    phone: str = Field(description="Owner's 10-digit primary mobile contact number.")
    registration_number: str = Field(description="Vehicle license plate registration number.")
    odometer: int = Field(description="Current vehicle kilometer odometer reading.")
    issue_type: str = Field(description="Description of problem, symptom, or scheduled service milestone.")
    preferred_center: Literal[
        "Worli", "Andheri", "Thane", "Kandivali", "Kurla", "Navi Mumbai",
        "Bandra", "Goregaon", "Borivali", "Dadar", "Chembur"
    ] = Field(description="Preferred authorized Mahindra service workshop location.")
    priority: Literal["High", "Medium", "Low"] = Field(
        default="Medium",
        description="Severity: 'High' for safety hazards/brakes/engine; 'Medium' for defects/noise; 'Low' for routine maintenance.",
    )
    status: Literal["New", "Service Appointment Scheduled", "Escalated"] = Field(
        default="Service Appointment Scheduled",
        description="Current ticket lifecycle status.",
    )
    case_origin: Literal["Chat", "Web", "Phone", "WhatsApp"] = Field(
        default="Chat",
        description="Intake channel through which the request was received.",
    )
    case_type: Optional[Literal["Periodic Maintenance", "Complaint"]] = Field(
        default=None,
        description="Classification of the service ticket.",
    )
