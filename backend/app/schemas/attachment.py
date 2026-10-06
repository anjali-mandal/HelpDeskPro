from pydantic import BaseModel
from datetime import datetime


class AttachmentResponse(BaseModel):

    id: int
    ticket_id: int
    uploaded_by: int
    file_name: str
    file_path: str
    file_type: str | None
    created_at: datetime | None

    class Config:
        from_attributes = True