from pydantic import BaseModel, Field
from datetime import datetime

class TicketCreate(BaseModel):
    title: str = Field(
        min_length=5,
        max_length=200
    )

    description: str = Field(
        min_length=10
    )

    category: str | None = None

    priority: str = "medium"


class TicketUpdate(BaseModel):

    title: str | None = Field(
        default=None,
        min_length=5,
        max_length=200
    )

    description: str | None = Field(
        default=None,
        min_length=10
    )

    category: str | None = None

    priority: str | None = None

    status: str | None = None

    assigned_to: int | None = None


class TicketAssign(BaseModel):

    engineer_id: int


class TicketResponse(BaseModel):

    id: int
    title: str
    description: str
    category: str
    priority: str
    status: str
    created_by: int
    assigned_to: int | None
    sla_deadline: object | None

    class Config:
        from_attributes = True


class TicketHistoryResponse(BaseModel):

    id: int
    ticket_id: int
    user_id: int
    action: str
    description: str | None
    created_at: datetime | None

    class Config:
        from_attributes = True