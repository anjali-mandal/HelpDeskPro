from pydantic import BaseModel, Field
from datetime import datetime


class CommentCreate(BaseModel):

    message: str = Field(
        min_length=1,
        max_length=2000
    )


class CommentResponse(BaseModel):

    id: int
    message: str
    ticket_id: int
    user_id: int
    user_name: str
    created_at: datetime | None

    class Config:
        from_attributes = True