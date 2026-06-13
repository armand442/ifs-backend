import logging
from datetime import datetime

from fastapi import FastAPI, Header, HTTPException, Depends

from config import APP_NAME, APP_VERSION, AI_MODE, API_SECRET, MONTHLY_LIMIT
from database import init_db, get_connection
from schemas import ChatIn, ChatOut, MessageOut
from services import (
    LIMIT_MESSAGE,
    get_used,
    inc_used,
    save_chat_message,
    mock_ifs_reply,
    get_recent_messages,
    get_conversation_context,
)

app = FastAPI(title=f"{APP_NAME} (MVP)")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ifs-backend")


def verify_api_key(x_api_key: str | None = Header(default=None)):
    if not API_SECRET:
        raise HTTPException(status_code=500, detail="API_SECRET is not configured")

    if x_api_key != API_SECRET:
        raise HTTPException(status_code=401, detail="Invalid API key")


def month_key(dt: datetime | None = None) -> str:
    dt = dt or datetime.utcnow()
    return dt.strftime("%Y-%m")


init_db()


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/version")
def version():
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "database": "postgresql",
        "ai": AI_MODE
    }


@app.get("/db-check", dependencies=[Depends(verify_api_key)])
def db_check():
    try:
        with get_connection() as con:
            with con.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()

        logger.info("Database health check successful")

        return {
            "database": "postgresql",
            "connected": True,
            "result": result[0]
        }

    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Database connection failed")


@app.get("/usage", dependencies=[Depends(verify_api_key)])
def usage(device_id: str):
    m = month_key()
    used = get_used(device_id, m)

    return {
        "device_id": device_id,
        "month": m,
        "used": used,
        "limit": MONTHLY_LIMIT,
        "remaining": max(0, MONTHLY_LIMIT - used)
    }

@app.get("/messages", response_model=list[MessageOut], dependencies=[Depends(verify_api_key)])
def messages(device_id: str, limit: int = 20):
    if limit < 1:
        limit = 1

    if limit > 50:
        limit = 50

    logger.info(f"Messages requested | device_id={device_id} | limit={limit}")

    return get_recent_messages(device_id, limit)

@app.post("/chat", response_model=ChatOut, dependencies=[Depends(verify_api_key)])
def chat(payload: ChatIn):
    logger.info(f"Chat request received | device_id={payload.device_id}")

    m = month_key()
    used = get_used(payload.device_id, m)
    context = get_conversation_context(payload.device_id)

    logger.info(
        f"Context loaded | device_id={payload.device_id} | messages={len(context)}"
    )

    if used >= MONTHLY_LIMIT:
        logger.warning(
            f"Monthly limit reached | device_id={payload.device_id} | used={used}"
        )

        return ChatOut(
            blocked=True,
            messages_used=used,
            limit=MONTHLY_LIMIT,
            reply=LIMIT_MESSAGE
        )

    new_used = inc_used(payload.device_id, m, 1)

    save_chat_message(payload.device_id, "user", payload.text)

    reply = mock_ifs_reply(payload.text)

    save_chat_message(payload.device_id, "assistant", reply)

    logger.info(
        f"Message counted | device_id={payload.device_id} | messages_used={new_used}"
    )

    return ChatOut(
        blocked=False,
        messages_used=new_used,
        limit=MONTHLY_LIMIT,
        reply=reply
    )