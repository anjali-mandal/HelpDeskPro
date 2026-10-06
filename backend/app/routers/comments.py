
from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from app.database.connection import get_db

from app.models.comment import Comment
from app.models.ticket import Ticket
from app.models.ticket_history import TicketHistory
from app.models.user import User

from app.schemas.comment import (
    CommentCreate,
    CommentResponse
)

from app.utils.dependencies import get_current_user

from app.services.notification_service import (
    create_notification
)


router = APIRouter(
    prefix="/tickets",
    tags=["Comments"]
)


# =====================================================
# ADD COMMENT
# =====================================================

@router.post(
    "/{ticket_id}/comments",
    response_model=CommentResponse
)
def add_comment(
    ticket_id: int,
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
    # PERMISSION CHECK
    # =================================================

    if current_user.role == "employee":

        if ticket.created_by != current_user.id:

            raise HTTPException(
                status_code=403,
                detail="You cannot comment on this ticket"
            )

    elif current_user.role == "engineer":

        if ticket.assigned_to != current_user.id:

            raise HTTPException(
                status_code=403,
                detail=(
                    "You are not assigned "
                    "to this ticket"
                )
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
    # CREATE COMMENT
    # =================================================

    new_comment = Comment(
        message=comment_data.message,
        ticket_id=ticket.id,
        user_id=current_user.id
    )

    db.add(new_comment)

    # =================================================
    # CREATE HISTORY
    # =================================================

    history = TicketHistory(
        ticket_id=ticket.id,
        user_id=current_user.id,
        action="comment_added",
        description=(
            f"{current_user.name} "
            f"added a comment"
        )
    )

    db.add(history)

    # =================================================
    # CREATE NOTIFICATION
    # =================================================

    recipient_id = None

    # Employee commented
    # → notify assigned engineer
    if current_user.role == "employee":

        if ticket.assigned_to is not None:

            recipient_id = ticket.assigned_to

    # Engineer commented
    # → notify ticket creator
    elif current_user.role == "engineer":

        recipient_id = ticket.created_by

    # Manager/Admin commented
    # → notify ticket creator
    elif current_user.role in [
        "manager",
        "admin"
    ]:

        recipient_id = ticket.created_by

    # Don't notify if recipient is same user
    if (
        recipient_id is not None
        and recipient_id != current_user.id
    ):

        notification = create_notification(
            db=db,
            user_id=recipient_id,
            title="New Ticket Comment",
            message=(
                f"{current_user.name} "
                f"commented on ticket "
                f"#{ticket.id}"
            ),
            ticket_id=ticket.id
        )

        db.add(notification)

    # =================================================
    # COMMIT
    # =================================================

    db.commit()

    db.refresh(new_comment)

    return new_comment


# =====================================================
# GET COMMENTS
# =====================================================

@router.get(
    "/{ticket_id}/comments",
    response_model=list[CommentResponse]
)
def get_comments(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
    # PERMISSION CHECK
    # =================================================

    if current_user.role == "employee":

        if ticket.created_by != current_user.id:

            raise HTTPException(
                status_code=403,
                detail="You cannot view these comments"
            )

    elif current_user.role == "engineer":

        if ticket.assigned_to != current_user.id:

            raise HTTPException(
                status_code=403,
                detail=(
                    "You are not assigned "
                    "to this ticket"
                )
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
    # GET COMMENTS
    # =================================================

    comments = db.query(
        Comment
    ).filter(
        Comment.ticket_id == ticket_id
    ).order_by(
        Comment.created_at.asc()
    ).all()

    return comments
