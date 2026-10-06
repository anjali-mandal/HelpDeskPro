from fastapi import APIRouter, Depends

from app.models.user import User
from app.schemas.ai import AISuggestionRequest, AISuggestionResponse
from app.services.ai_service import suggest_issue
from app.utils.dependencies import get_current_user


router = APIRouter(prefix="/ai", tags=["AI Assistance"])


@router.post("/suggest", response_model=AISuggestionResponse)
def suggest_ticket(
    request: AISuggestionRequest,
    current_user: User = Depends(get_current_user),
):
    return suggest_issue(request.title, request.description, request.priority)