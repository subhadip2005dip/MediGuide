from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes import webhooks
from src.routes import triage
from src.database.db import init_db

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

@app.on_event("startup")
async def startup():
    """Initialize database tables on startup"""
    await init_db()

app.include_router(webhooks.router, prefix="/webhooks")
app.include_router(triage.router, prefix="/triage")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
