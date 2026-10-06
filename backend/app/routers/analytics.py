from collections import Counter
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.ticket import Ticket
from app.models.user import User
from app.utils.dependencies import require_role


router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview")
def overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("manager", "admin")),
):
    tickets = db.query(Ticket).all()
    active = [ticket for ticket in tickets if ticket.status not in {"resolved", "closed"}]
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    overdue = [ticket for ticket in active if ticket.sla_deadline and ticket.sla_deadline < now]
    resolved = [ticket for ticket in tickets if ticket.resolved_at]
    durations = [(ticket.resolved_at - ticket.created_at).total_seconds() / 3600 for ticket in resolved if ticket.created_at]
    return {
        "total": len(tickets),
        "open": len(active),
        "resolved": len(resolved),
        "sla_breached": len(overdue),
        "average_resolution_hours": round(sum(durations) / len(durations), 2) if durations else 0,
        "by_category": dict(Counter(ticket.category for ticket in tickets)),
        "by_priority": dict(Counter(ticket.priority for ticket in tickets)),
        "tickets_per_engineer": {
            user.name: sum(ticket.assigned_to == user.id for ticket in tickets)
            for user in db.query(User).filter(User.role == "engineer").all()
        },
    }