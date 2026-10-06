from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.utils.dependencies import (
    get_current_user,
    require_role
)


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


class RoleUpdate(BaseModel):
    role: str


@router.get("/me")
def get_my_profile(
    current_user: User = Depends(get_current_user)
):

    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role
    }


@router.get("/engineer-only")
def engineer_api(
    current_user: User = Depends(
        require_role("engineer")
    )
):

    return {
        "message": "Welcome Engineer",
        "user": current_user.name
    }


@router.get("/manager-only")
def manager_api(
    current_user: User = Depends(
        require_role("manager")
    )
):

    return {
        "message": "Welcome Manager",
        "user": current_user.name
    }


@router.get("/staff")
def staff_api(
    current_user: User = Depends(
        require_role("engineer", "manager", "admin")
    )
):

    return {
        "message": "Staff access granted",
        "user": current_user.name,
        "role": current_user.role
    }


@router.get("/engineers")
def list_engineers(
    current_user: User = Depends(
        require_role("manager", "admin")
    ),
    db: Session = Depends(get_db)
):
    return db.query(User).filter(
        User.role == "engineer"
    ).order_by(User.name.asc()).all()


@router.get("", dependencies=[Depends(require_role("admin"))])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.name.asc()).all()


@router.patch("/{user_id}/role")
def update_user_role(
    user_id: int,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    if payload.role not in {"employee", "engineer", "manager", "admin"}:
        raise HTTPException(status_code=422, detail="Invalid role")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user