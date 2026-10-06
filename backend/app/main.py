import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.database.connection import engine, SessionLocal, ensure_schema
from app.database.base import Base
from app.utils.security import hash_password

from app.models import User
from app.routers import (
    auth,
    users,
    tickets,
    comments,
    attachments,
    user_notifications
)
from app.routers import ai, analytics
from app.services.realtime import hub
from app.services.sla_worker import monitor_sla
from app.utils.jwt import verify_token

Base.metadata.create_all(bind=engine)
ensure_schema()


def seed_demo_users():
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            return

        demo_users = [
            {
                "name": "Employee User",
                "email": "employee@helpdeskpro.com",
                "password": "employee123",
                "role": "employee"
            },
            {
                "name": "Engineer User",
                "email": "engineer@helpdeskpro.com",
                "password": "engineer123",
                "role": "engineer"
            },
            {
                "name": "Manager User",
                "email": "manager@helpdeskpro.com",
                "password": "manager123",
                "role": "manager"
            },
            {
                "name": "Admin User",
                "email": "admin@helpdeskpro.com",
                "password": "admin123",
                "role": "admin"
            }
        ]

        for item in demo_users:
            db.add(User(
                name=item["name"],
                email=item["email"],
                password_hash=hash_password(item["password"]),
                role=item["role"]
            ))

        db.commit()
    finally:
        db.close()


seed_demo_users()


@asynccontextmanager
async def lifespan(application: FastAPI):
    hub.set_loop(asyncio.get_running_loop())
    worker = None if os.getenv("REDIS_URL") else asyncio.create_task(monitor_sla())
    try:
        yield
    finally:
        if worker:
            worker.cancel()
            await asyncio.gather(worker, return_exceptions=True)
        hub.loop = None


app = FastAPI(title="HelpDeskPro API", lifespan=lifespan)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_URL",
        "http://localhost:5174,http://127.0.0.1:5174"
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tickets.router)
app.include_router(comments.router)
app.include_router(
    attachments.router
)
app.include_router(
    user_notifications.router
)
app.include_router(ai.router)
app.include_router(analytics.router)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    payload = verify_token(token) if token else None
    user_id = payload.get("user_id") if payload else None
    if not user_id:
        await websocket.close(code=1008)
        return
    await hub.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        hub.disconnect(user_id, websocket)

@app.get("/")
def root():

    return {
        "message": "HelpDeskPro API is running"
    }