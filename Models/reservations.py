from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID

class ReservationExtraction(BaseModel):
    customer_name: Optional[str] = None
    party_size: Optional[int] = None
    reservation_time: Optional[datetime] = None
    special_request: Optional[str] = None
    items: Optional[list[dict]] = None
    pickup_time: Optional[datetime] = None
    reason: Optional[str] = None

class CallOutputValidated(BaseModel):
    call_id: UUID
    customer_name: Optional[str] = None
    phone_number: Optional[str] = None
    party_size: Optional[int] = None
    reservation_time: Optional[datetime] = None
    special_request: Optional[str] = None
    pickup_time: Optional[datetime] = None
    reason: Optional[str] = None
    missing_fields: Optional[list[str]] = None
    is_complete: bool = False

class CallLogsValidated(BaseModel):
    call_id: UUID
    summary: str
    transcript: str
    recording_url: str
    phone_number: str
    started_at: datetime
    ended_at: datetime
    duration_seconds: float
    ended_reason: str
    structured_output: Optional[dict] = None
    call_type: Optional[str] = None

class ItemValidated(BaseModel):
    order_id: Optional[int] = None
    item_number: Optional[str] = None
    item_name: Optional[str] = None
    quantity: Optional[int] = None

class ReservationOutput(BaseModel):
    id: int
    name: str
    phone_number: str
    number_of_people: int
    reservation_time: datetime

