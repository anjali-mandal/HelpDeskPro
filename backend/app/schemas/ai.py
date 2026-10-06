from pydantic import BaseModel, Field


class AISuggestionRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10)
    priority: str | None = None


class AISuggestionResponse(BaseModel):
    category: str
    priority: str
    confidence: float
    troubleshooting: list[str]
    disclaimer: str