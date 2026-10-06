
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db

from app.models.ticket import Ticket
from app.models.user import User
from app.models.ticket_history import TicketHistory

from app.schemas.ticket import (
    TicketCreate,
    TicketUpdate,
    TicketResponse,
    TicketAssign,
    TicketHistoryResponse
)

from app.utils.dependencies import (
    get_current_user,
    require_role
)

from app.utils.ticket_rules import (
    is_valid_status,
    is_valid_priority,
    can_change_status
)

from app.services.notification_service import (
    create_notification
)


router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)


# =====================================================
# CREATE TICKET
# =====================================================

@router.post(
    "/",
    response_model=TicketResponse
)
def create_ticket(
    ticket: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if not is_valid_priority(ticket.priority):
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid priority. "
                "Allowed values: "
                "low, medium, high, critical"
            )
        )

    new_ticket = Ticket(
        title=ticket.title,
        description=ticket.description,
        category=ticket.category,
        priority=ticket.priority,
        status="open",
        created_by=current_user.id
    )

    db.add(new_ticket)

    db.commit()

    db.refresh(new_ticket)

    return new_ticket


# =====================================================
# GET ALL TICKETS
# =====================================================

@router.get(
    "/",
    response_model=list[TicketResponse]
)
def get_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role == "employee":

        tickets = db.query(Ticket).filter(
            Ticket.created_by == current_user.id
        ).all()

    elif current_user.role == "engineer":

        tickets = db.query(Ticket).filter(
            Ticket.assigned_to == current_user.id
        ).all()

    elif current_user.role in [
        "manager",
        "admin"
    ]:

        tickets = db.query(Ticket).all()

    else:

        tickets = []

    return tickets


# =====================================================
# GET TICKET HISTORY
# =====================================================

@router.get(
    "/{ticket_id}/history",
    response_model=list[TicketHistoryResponse]
)
def get_ticket_history(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id
    ).first()

    if not ticket:

        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    # Employee permission
    if current_user.role == "employee":

        if ticket.created_by != current_user.id:

            raise HTTPException(
                status_code=403,
                detail="You cannot view this history"
            )

    # Engineer permission
    elif current_user.role == "engineer":

        if ticket.assigned_to != current_user.id:

            raise HTTPException(
                status_code=403,
                detail=(
                    "You are not assigned "
                    "to this ticket"
                )
            )

    # Manager/Admin
    elif current_user.role in [
        "manager",
        "admin"
    ]:

        pass

    else:

        raise HTTPException(
            status_code=403,
            detail="Invalid role"
        )

    history = db.query(
        TicketHistory
    ).filter(
        TicketHistory.ticket_id == ticket_id
    ).order_by(
        TicketHistory.created_at.asc()
    ).all()

    return history


# =====================================================
# GET SINGLE TICKET
# =====================================================

@router.get(
    "/{ticket_id}",
    response_model=TicketResponse
)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id
    ).first()

    if not ticket:

        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    # Employee permission
    if current_user.role == "employee":

        if ticket.created_by != current_user.id:

            raise HTTPException(
                status_code=403,
                detail=(
                    "You don't have permission "
                    "to view this ticket"
                )
            )

    # Engineer permission
    elif current_user.role == "engineer":

        if ticket.assigned_to != current_user.id:

            raise HTTPException(
                status_code=403,
                detail=(
                    "You don't have permission "
                    "to view this ticket"
                )
            )

    # Manager/Admin
    elif current_user.role in [
        "manager",
        "admin"
    ]:

        pass

    else:

        raise HTTPException(
            status_code=403,
            detail="Invalid role"
        )

    return ticket


# =====================================================
# UPDATE TICKET
# =====================================================

@router.put(
    "/{ticket_id}",
    response_model=TicketResponse
)
def update_ticket(
    ticket_id: int,
    ticket_data: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id
    ).first()

    if not ticket:

        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    # =================================================
    # PERMISSION CHECK
    # =================================================

    if current_user.role == "employee":

        if ticket.created_by != current_user.id:

            raise HTTPException(
                status_code=403,
                detail="You cannot update this ticket"
            )

        if ticket_data.priority is not None:

            raise HTTPException(
                status_code=403,
                detail="Employee cannot change priority"
            )

        if ticket_data.status is not None:

            raise HTTPException(
                status_code=403,
                detail="Employee cannot change status"
            )

        if ticket_data.assigned_to is not None:

            raise HTTPException(
                status_code=403,
                detail="Employee cannot assign ticket"
            )

    elif current_user.role == "engineer":

        if ticket.assigned_to != current_user.id:

            raise HTTPException(
                status_code=403,
                detail="You cannot update this ticket"
            )

        if ticket_data.assigned_to is not None:

            raise HTTPException(
                status_code=403,
                detail="Engineer cannot assign tickets"
            )

    elif current_user.role in [
        "manager",
        "admin"
    ]:

        pass

    else:

        raise HTTPException(
            status_code=403,
            detail="Invalid role"
        )

    # =================================================
    # PRIORITY VALIDATION
    # =================================================

    if ticket_data.priority is not None:

        if not is_valid_priority(
            ticket_data.priority
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid priority. "
                    "Allowed values: "
                    "low, medium, high, critical"
                )
            )

    # =================================================
    # STATUS VALIDATION
    # =================================================

    if ticket_data.status is not None:

        if not is_valid_status(
            ticket_data.status
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid status. "
                    "Allowed values: "
                    "open, assigned, "
                    "in_progress, resolved, closed"
                )
            )

    # =================================================
    # STATUS TRANSITION VALIDATION
    # =================================================

    if ticket_data.status is not None:

        if ticket_data.status != ticket.status:

            if not can_change_status(
                ticket.status,
                ticket_data.status
            ):

                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Cannot change status "
                        f"from '{ticket.status}' "
                        f"to '{ticket_data.status}'"
                    )
                )

    # Save old values
    old_status = ticket.status
    old_priority = ticket.priority

    new_status = ticket_data.status
    new_priority = ticket_data.priority

    # =================================================
    # UPDATE FIELDS
    # =================================================

    update_data = ticket_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():

        setattr(
            ticket,
            field,
            value
        )

    # =================================================
    # STATUS HISTORY
    # =================================================

    if (
        new_status is not None
        and new_status != old_status
    ):

        history = TicketHistory(
            ticket_id=ticket.id,
            user_id=current_user.id,
            action="status_changed",
            description=(
                f"Status changed from "
                f"{old_status} to {new_status}"
            )
        )

        db.add(history)

    # =================================================
    # PRIORITY HISTORY
    # =================================================

    if (
        new_priority is not None
        and new_priority != old_priority
    ):

        history = TicketHistory(
            ticket_id=ticket.id,
            user_id=current_user.id,
            action="priority_changed",
            description=(
                f"Priority changed from "
                f"{old_priority} to {new_priority}"
            )
        )

        db.add(history)

    # =================================================
    # NOTIFICATION FOR STATUS CHANGE
    # =================================================

    if (
        new_status is not None
        and new_status != old_status
    ):

        # Notify ticket creator
        if ticket.created_by != current_user.id:

            notification = create_notification(
                db=db,
                user_id=ticket.created_by,
                title="Ticket Status Updated",
                message=(
                    f"Ticket #{ticket.id} status "
                    f"changed from "
                    f"{old_status} to {new_status}"
                ),
                ticket_id=ticket.id
            )

            db.add(notification)

    # =================================================
    # NOTIFICATION FOR PRIORITY CHANGE
    # =================================================

    if (
        new_priority is not None
        and new_priority != old_priority
    ):

        # Notify assigned engineer
        if ticket.assigned_to is not None:

            if ticket.assigned_to != current_user.id:

                notification = create_notification(
                    db=db,
                    user_id=ticket.assigned_to,
                    title="Ticket Priority Updated",
                    message=(
                        f"Ticket #{ticket.id} "
                        f"priority changed from "
                        f"{old_priority} to "
                        f"{new_priority}"
                    ),
                    ticket_id=ticket.id
                )

                db.add(notification)

    db.commit()

    db.refresh(ticket)

    return ticket


# =====================================================
# ASSIGN TICKET
# =====================================================

@router.patch(
    "/{ticket_id}/assign",
    response_model=TicketResponse
)
def assign_ticket(
    ticket_id: int,
    assignment: TicketAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            "manager",
            "admin"
        )
    )
):

    # =================================================
    # FIND TICKET
    # =================================================

    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id
    ).first()

    if not ticket:

        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    # =================================================
    # FIND ENGINEER
    # =================================================

    engineer = db.query(User).filter(
        User.id == assignment.engineer_id
    ).first()

    if not engineer:

        raise HTTPException(
            status_code=404,
            detail="Engineer not found"
        )

    # =================================================
    # CHECK ENGINEER ROLE
    # =================================================

    if engineer.role != "engineer":

        raise HTTPException(
            status_code=400,
            detail="Selected user is not an engineer"
        )

    # =================================================
    # CHECK TICKET STATUS
    # =================================================

    if ticket.status != "open":

        raise HTTPException(
            status_code=400,
            detail=(
                f"Ticket cannot be assigned "
                f"when status is '{ticket.status}'"
            )
        )

    # =================================================
    # ASSIGN TICKET
    # =================================================

    ticket.assigned_to = engineer.id

    ticket.status = "assigned"

    # =================================================
    # CREATE HISTORY
    # =================================================

    history = TicketHistory(
        ticket_id=ticket.id,
        user_id=current_user.id,
        action="assigned",
        description=(
            f"Ticket assigned to engineer "
            f"{engineer.name}"
        )
    )

    db.add(history)

    # =================================================
    # CREATE NOTIFICATION
    # =================================================

    notification = create_notification(
        db=db,
        user_id=engineer.id,
        title="New Ticket Assigned",
        message=(
            f"Ticket #{ticket.id} "
            f"has been assigned to you"
        ),
        ticket_id=ticket.id
    )

    db.add(notification)

    # =================================================
    # COMMIT EVERYTHING
    # =================================================

    db.commit()

    db.refresh(ticket)

    return ticket
