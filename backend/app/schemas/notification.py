from pydantic import BaseModel
from datetime import datetime


class NotificationResponse(BaseModel):

    id: int
    user_id: int
    ticket_id: int | None
    title: str
    message: str
    is_read: bool
    created_at: datetime | None

    class Config:
        from_attributes = True