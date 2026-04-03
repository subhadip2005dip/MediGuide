from fastapi import APIRouter, Request, HTTPException, Depends
from svix.webhooks import Webhook
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import os
import json
from dotenv import load_dotenv
from ..models.models import User
from ..database.db import get_db

load_dotenv()

router = APIRouter()

@router.post("/clerk")
async def handle_user_created(request: Request, db: AsyncSession = Depends(get_db)):
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
        clerk_id = user_data.get("id")
        email = user_data.get("email_addresses", [{}])[0].get("email_address", "")
        first_name = user_data.get("first_name", "")
        last_name = user_data.get("last_name", "")
        name = f"{first_name} {last_name}".strip()
        avatar_url = user_data.get("image_url", "")

        stmt = select(User).where(User.clerk_id == clerk_id)
        result = await db.execute(stmt)
        existing_user = result.scalars().first()

        if existing_user:
            existing_user.email = email
            existing_user.name = name
            existing_user.avatar_url = avatar_url
            await db.commit()
            await db.refresh(existing_user)
            return {"status": "success", "user_id": existing_user.id}

        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        email_exists = result.scalars().first()

        if email_exists:
            email_exists.clerk_id = clerk_id
            email_exists.name = name
            email_exists.avatar_url = avatar_url
            await db.commit()
            await db.refresh(email_exists)
            return {"status": "success", "user_id": email_exists.id}

        new_user = User(
            clerk_id=clerk_id,
            email=email,
            name=name,
            avatar_url=avatar_url,
            created_at=datetime.utcnow()
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        return {"status": "success", "user_id": new_user.id}
    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=401, detail=str(e))
