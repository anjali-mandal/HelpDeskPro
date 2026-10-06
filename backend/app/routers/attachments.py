import os
import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File
)

from sqlalchemy.orm import Session
from fastapi.responses import FileResponse

from app.database.connection import get_db

from app.models.ticket import Ticket
from app.models.user import User
from app.models.ticket_attachment import TicketAttachment
from app.models.ticket_history import TicketHistory

from app.schemas.attachment import AttachmentResponse

from app.utils.dependencies import get_current_user


router = APIRouter(
    prefix="/tickets",
    tags=["Attachments"]
)


UPLOAD_DIR = "uploads"


# Create uploads folder
os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)


# =========================
# UPLOAD ATTACHMENT
# =========================

@router.post(
    "/{ticket_id}/attachments",
    response_model=AttachmentResponse
)
async def upload_attachment(
    ticket_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # ---------------------------------
    # 1. Find ticket
    # ---------------------------------

    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id
    ).first()

    if not ticket:

        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )


    # ---------------------------------
    # 2. Permission check
    # ---------------------------------

    if current_user.role == "employee":

        if ticket.created_by != current_user.id:

            raise HTTPException(
                status_code=403,
                detail="You cannot upload to this ticket"
            )


    elif current_user.role == "engineer":

        if ticket.assigned_to != current_user.id:

            raise HTTPException(
                status_code=403,
                detail="You are not assigned to this ticket"
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


    # ---------------------------------
    # 3. Validate file
    # ---------------------------------

    allowed_types = [
        "image/jpeg",
        "image/png",
        "application/pdf",
        "text/plain"
    ]

    if file.content_type not in allowed_types:

        raise HTTPException(
            status_code=400,
            detail=(
                "File type not allowed. "
                "Allowed: JPG, PNG, PDF, TXT"
            )
        )


    # ---------------------------------
    # 4. Read file
    # ---------------------------------

    file_data = await file.read()


    # ---------------------------------
    # 5. Check file size
    # ---------------------------------

    max_size = 5 * 1024 * 1024

    if len(file_data) > max_size:

        raise HTTPException(
            status_code=400,
            detail="File size cannot exceed 5 MB"
        )


    # ---------------------------------
    # 6. Generate unique filename
    # ---------------------------------

    extension = ""

    if "." in file.filename:

        extension = "." + file.filename.split(".")[-1]


    unique_name = (
        f"{uuid.uuid4()}{extension}"
    )


    file_path = os.path.join(
        UPLOAD_DIR,
        unique_name
    )


    # ---------------------------------
    # 7. Save file
    # ---------------------------------

    with open(
        file_path,
        "wb"
    ) as buffer:

        buffer.write(file_data)


    # ---------------------------------
    # 8. Save database record
    # ---------------------------------

    attachment = TicketAttachment(
        ticket_id=ticket.id,
        uploaded_by=current_user.id,
        file_name=file.filename,
        file_path=file_path,
        file_type=file.content_type
    )

    db.add(attachment)


    # ---------------------------------
    # 9. Add history
    # ---------------------------------

    history = TicketHistory(
        ticket_id=ticket.id,
        user_id=current_user.id,
        action="attachment_added",
        description=(
            f"File attached: "
            f"{file.filename}"
        )
    )

    db.add(history)


    # ---------------------------------
    # 10. Commit
    # ---------------------------------

    db.commit()

    db.refresh(attachment)


    return attachment

@router.get(
    "/{ticket_id}/attachments",
    response_model=list[AttachmentResponse]
)
def get_attachments(
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

    # Permission check
    if current_user.role == "employee":

        if ticket.created_by != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You cannot view these attachments"
            )

    elif current_user.role == "engineer":

        if ticket.assigned_to != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You are not assigned to this ticket"
            )

    elif current_user.role in ["manager", "admin"]:
        pass

    else:
        raise HTTPException(
            status_code=403,
            detail="Invalid role"
        )

    attachments = db.query(
        TicketAttachment
    ).filter(
        TicketAttachment.ticket_id == ticket_id
    ).all()

    return attachments

@router.get(
    "/attachments/{attachment_id}/download"
)
def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    attachment = db.query(
        TicketAttachment
    ).filter(
        TicketAttachment.id == attachment_id
    ).first()

    if not attachment:
        raise HTTPException(
            status_code=404,
            detail="Attachment not found"
        )

    ticket = db.query(Ticket).filter(
        Ticket.id == attachment.ticket_id
    ).first()

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    # Permission check
    if current_user.role == "employee":

        if ticket.created_by != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You cannot download this file"
            )

    elif current_user.role == "engineer":

        if ticket.assigned_to != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You are not assigned to this ticket"
            )

    elif current_user.role in ["manager", "admin"]:
        pass

    else:
        raise HTTPException(
            status_code=403,
            detail="Invalid role"
        )

    if not os.path.exists(attachment.file_path):
        raise HTTPException(
            status_code=404,
            detail="File not found on server"
        )

    return FileResponse(
        path=attachment.file_path,
        filename=attachment.file_name,
        media_type=attachment.file_type
    )    

