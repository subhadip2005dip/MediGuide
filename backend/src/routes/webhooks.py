from fastapi import APIRouter, Request, HTTPException, Depends
from svix.webhooks import Webhook
import os
import json
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

@router.post("/clerk")
async def handle_user_created(request: Request):
    webhook_secret = os.getenv("CLERK_WEBHOOK_SECRET")

    if not webhook_secret:
        raise HTTPException(status_code=500, detail="CLERK_WEBHOOK_SECRET not set")

    body = await request.body()
    payload = body.decode("utf-8")
    headers = dict(request.headers)

    try:
        wh = Webhook(webhook_secret)
        wh.verify(payload, headers)

        data = json.loads(payload)

        if data.get("type") != "user.created":
            return {"status": "ignored"}

        user_data = data.get("data", {})
        user_id = user_data.get("id")

        print(f"Received user.created event for user ID: {user_id}")
        print(f"Full event data: {json.dumps(data, indent=2)}")

        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
