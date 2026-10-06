from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database.base import Base


class Ticket(Base):

    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(200), nullable=False)

    description = Column(Text, nullable=False)

    category = Column(String(50), nullable=False)

    priority = Column(String(20), default="medium")

    status = Column(String(20), default="open")

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)

    sla_deadline = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=True)

    updated_at = Column(DateTime, nullable=True)

    resolved_at = Column(DateTime, nullable=True)

    sla_breached = Column(Boolean, default=False, nullable=False)
    
    creator = relationship(
        "User",
        foreign_keys=[created_by],
        back_populates="created_tickets"
    )

    assignee = relationship(
        "User",
        foreign_keys=[assigned_to],
        back_populates="assigned_tickets"
    )

    comments = relationship(
        "Comment",
        back_populates="ticket",
        cascade="all, delete-orphan"
    )