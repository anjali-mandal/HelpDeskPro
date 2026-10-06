import asyncio
from datetime import datetime, timezone

from app.database.connection import SessionLocal
from app.models.notification import Notification
from app.models.ticket import Ticket
from app.models.user import User
from app.services.realtime import hub


def check_sla_breaches() -> int:
    db = SessionLocal()
    breached_count = 0
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        tickets = db.query(Ticket).filter(
            Ticket.sla_deadline.isnot(None),
            Ticket.sla_deadline < now,
            Ticket.status.notin_(["resolved", "closed"]),
            Ticket.sla_breached.is_(False),
        ).all()
        manager_ids = {user.id for user in db.query(User).filter(User.role.in_(["manager", "admin"])).all()}
        for ticket in tickets:
            ticket.sla_breached = True
            breached_count += 1
            for manager_id in manager_ids:
                db.add(Notification(
                    user_id=manager_id,
                    ticket_id=ticket.id,
                    title="SLA breached",
                    message=f"Ticket #{ticket.id} exceeded its {ticket.priority} SLA.",
                ))
            hub.publish_nowait(manager_ids | ({ticket.created_by} if ticket.created_by else set()), {
                "type": "sla_breached", "ticket_id": ticket.id,
            })
        if tickets:
            db.commit()
        return breached_count
    finally:
        db.close()


async def monitor_sla(interval_seconds: int = 60):
    while True:
        check_sla_breaches()
        await asyncio.sleep(interval_seconds)