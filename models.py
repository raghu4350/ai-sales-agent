from pydantic import BaseModel
from typing import Optional


class LeadData(BaseModel):

    customer_name: Optional[str] = "Unknown"
    customer_email: Optional[str] = "Not provided"   # NEW: email field
    customer_need: str
    budget: str
    urgency: str
    callback_required: bool
    lead_status: Optional[str] = "MEDIUM"