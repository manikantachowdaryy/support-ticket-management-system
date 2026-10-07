from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.attachments import router as attachments_router
from app.routers.audit_logs import router as audit_logs_router
from app.routers.auth import router as auth_router
from app.routers.categories import router as categories_router
from app.routers.comments import router as comments_router
from app.routers.dashboard import router as dashboard_router
from app.routers.notifications import router as notifications_router
from app.routers.tickets import router as tickets_router
from app.routers.users import router as users_router


app = FastAPI(
    title="Support Ticket Management System API",
    description="Backend API for a Support Ticket Management System",
    version="1.0.0",
)


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(categories_router)
app.include_router(tickets_router)
app.include_router(comments_router)
app.include_router(attachments_router)
app.include_router(notifications_router)
app.include_router(audit_logs_router)
app.include_router(dashboard_router)


@app.get("/")
def root():
    return {
        "message": "Support Ticket Management System API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }