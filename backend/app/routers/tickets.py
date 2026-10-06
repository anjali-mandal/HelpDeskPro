from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.ticket import Ticket
from app.models.ticket_history import TicketHistory
from app.models.notification import Notification
from app.models.user import User
from app.schemas.ticket import (
    TicketAssign,
    TicketCreate,
    TicketHistoryResponse,
    TicketResponse,
    TicketUpdate,
)
from app.utils.dependencies import get_current_user
from app.utils.sla import calculate_sla_deadline
from app.utils.ticket_rules import can_change_status
from app.services.ai_service import suggest_issue
from app.services.realtime import hub


router = APIRouter(prefix="/tickets", tags=["Tickets"])

ALLOWED_PRIORITIES = {"low", "medium", "high", "critical"}
ALLOWED_STATUSES = {"open", "in_progress", "resolved", "closed"}


def _get_ticket(ticket_id: int, db: Session) -> Ticket:
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


def _can_access(ticket: Ticket, user: User) -> bool:
    return user.role in {"manager", "admin"} or (
        user.role == "employee" and ticket.created_by == user.id
    ) or (user.role == "engineer" and ticket.assigned_to == user.id)


def _validate_priority(priority: str | None) -> None:
    if priority is not None and priority not in ALLOWED_PRIORITIES:
        raise HTTPException(status_code=422, detail="Invalid priority")


def _validate_status(status: str | None) -> None:
    if status is not None and status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=422, detail="Invalid status")


def _add_history(
    db: Session,
    ticket: Ticket,
    user: User,
    action: str,
    description: str,
) -> None:
    db.add(
        TicketHistory(
            ticket_id=ticket.id,
            user_id=user.id,
            action=action,
            description=description,
        )
    )


@router.post("", response_model=TicketResponse, status_code=201)
def create_ticket(
    ticket_data: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _validate_priority(ticket_data.priority)
    now = datetime.now(timezone.utc)
    suggestion = suggest_issue(ticket_data.title, ticket_data.description, ticket_data.priority)
    ticket = Ticket(
        title=ticket_data.title,
        description=ticket_data.description,
        category=ticket_data.category or suggestion["category"],
        priority=suggestion["priority"],
        status="open",
        created_by=current_user.id,
        created_at=now,
        updated_at=now,
        sla_deadline=calculate_sla_deadline(ticket_data.priority),
    )
    try:
        db.add(ticket)
        db.flush()
        _add_history(db, ticket, current_user, "created", "Ticket created")
        managers = db.query(User).filter(User.role.in_(["manager", "admin"])).all()
        for manager in managers:
            db.add(Notification(
                user_id=manager.id,
                ticket_id=ticket.id,
                title="New ticket created",
                message=f"{current_user.name} created ticket #{ticket.id}",
            ))
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Ticket could not be created. Please try again.",
        ) from error

    db.refresh(ticket)
    recipient_ids = {user.id for user in managers} | {current_user.id}
    hub.publish_nowait(recipient_ids, {"type": "ticket_created", "ticket_id": ticket.id})
    return ticket


@router.get("", response_model=list[TicketResponse])
def list_tickets(
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _validate_status(status)
    query = db.query(Ticket)
    if current_user.role == "employee":
        query = query.filter(Ticket.created_by == current_user.id)
    elif current_user.role == "engineer":
        query = query.filter(Ticket.assigned_to == current_user.id)
    elif current_user.role not in {"manager", "admin"}:
        raise HTTPException(status_code=403, detail="Invalid role")
    if status is not None:
        query = query.filter(Ticket.status == status)
    return query.order_by(Ticket.created_at.desc()).all()


@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = _get_ticket(ticket_id, db)
    if not _can_access(ticket, current_user):
        raise HTTPException(status_code=403, detail="You cannot access this ticket")
    return ticket


@router.get("/{ticket_id}/history", response_model=list[TicketHistoryResponse])
def get_ticket_history(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = _get_ticket(ticket_id, db)
    if not _can_access(ticket, current_user):
        raise HTTPException(status_code=403, detail="You cannot access this ticket history")
    return db.query(TicketHistory).filter(
        TicketHistory.ticket_id == ticket_id
    ).order_by(TicketHistory.created_at.asc()).all()


@router.patch("/{ticket_id}", response_model=TicketResponse)
def update_ticket(
    ticket_id: int,
    ticket_data: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = _get_ticket(ticket_id, db)
    if not _can_access(ticket, current_user):
        raise HTTPException(status_code=403, detail="You cannot update this ticket")
    _validate_priority(ticket_data.priority)
    _validate_status(ticket_data.status)

    if current_user.role == "employee" and (
        ticket_data.status is not None
        or ticket_data.priority is not None
        or ticket_data.assigned_to is not None
    ):
        raise HTTPException(status_code=403, detail="Employees cannot change ticket workflow")
    if current_user.role == "engineer" and (
        ticket_data.priority is not None or ticket_data.assigned_to is not None
    ):
        raise HTTPException(status_code=403, detail="Engineers cannot change priority or assignment")

    if current_user.role == "engineer" and ticket_data.status is not None:
        if not can_change_status(ticket.status, ticket_data.status):
            raise HTTPException(status_code=409, detail="Invalid status transition")

    changes = ticket_data.model_dump(exclude_unset=True)
    changes.pop("assigned_to", None)
    for field, value in changes.items():
        setattr(ticket, field, value)
    if ticket_data.status == "resolved":
        ticket.resolved_at = datetime.now(timezone.utc)
    if ticket_data.status is not None and ticket.created_by != current_user.id:
        db.add(Notification(
            user_id=ticket.created_by,
            ticket_id=ticket.id,
            title="Ticket status updated",
            message=f"Ticket #{ticket.id} is now {ticket_data.status.replace('_', ' ')}",
        ))
    ticket.updated_at = datetime.now(timezone.utc)
    _add_history(db, ticket, current_user, "updated", "Ticket updated")
    db.commit()
    db.refresh(ticket)
    recipients = {ticket.created_by}
    if ticket.assigned_to:
        recipients.add(ticket.assigned_to)
    hub.publish_nowait(recipients, {"type": "ticket_updated", "ticket_id": ticket.id})
    return ticket


@router.post("/{ticket_id}/assign", response_model=TicketResponse)
def assign_ticket(
    ticket_id: int,
    assignment: TicketAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in {"manager", "admin"}:
        raise HTTPException(status_code=403, detail="Only managers and admins can assign tickets")
    ticket = _get_ticket(ticket_id, db)
    engineer = db.query(User).filter(
        User.id == assignment.engineer_id,
        User.role == "engineer",
    ).first()
    if engineer is None:
        raise HTTPException(status_code=404, detail="Engineer not found")
    ticket.assigned_to = engineer.id
    if ticket.status == "open":
        ticket.status = "assigned"
    ticket.updated_at = datetime.now(timezone.utc)
    _add_history(
        db,
        ticket,
        current_user,
        "assigned",
        f"Assigned to {engineer.name}",
    )
    db.add(Notification(
        user_id=engineer.id,
        ticket_id=ticket.id,
        title="Ticket assigned to you",
        message=f"Ticket #{ticket.id} was assigned to you",
    ))
    db.commit()
    db.refresh(ticket)
    hub.publish_nowait({ticket.created_by, engineer.id}, {"type": "ticket_assigned", "ticket_id": ticket.id})
    return ticket
