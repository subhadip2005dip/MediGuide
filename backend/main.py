from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes import webhooks

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(webhooks.router, prefix="/webhooks")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
