import os
import psycopg2
from datetime import datetime
from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel, Field

app = FastAPI(title="IFS Assistant Backend (MVP)")

MONTHLY_LIMIT = int(os.getenv("MONTHLY_MESSAGE_LIMIT_FREE", "120"))
DATABASE_URL = os.getenv("DATABASE_URL")
API_SECRET = os.getenv("API_SECRET")

def verify_api_key(x_api_key: str | None = Header(default=None)):
    if not API_SECRET:
        raise HTTPException(status_code=500, detail="API_SECRET is not configured")
    if x_api_key != API_SECRET:
        raise HTTPException(status_code=401, detail="Invalid API key")

LIMIT_MESSAGE = (
    "Ai ajuns la limita de mesaje disponibile pentru această perioadă. "
    "Poți activa un plan extins pentru a continua sau poți nota ce apare și aduce în ședință."
)

def init_db():
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS usage (
                device_id TEXT NOT NULL,
                month TEXT NOT NULL,
                messages_used INTEGER NOT NULL,
                PRIMARY KEY (device_id, month)
            )
            """)
        con.commit()


def month_key(dt: datetime | None = None) -> str:
    dt = dt or datetime.utcnow()
    return dt.strftime("%Y-%m")

def get_connection():
    if not DATABASE_URL:
        raise Exception("DATABASE_URL is not configured")

    return psycopg2.connect(DATABASE_URL)


def get_used(device_id: str, month: str) -> int:
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute(
                "SELECT messages_used FROM usage WHERE device_id=%s AND month=%s",
                (device_id, month)
            )

            row = cur.fetchone()
            return int(row[0]) if row else 0


def inc_used(device_id: str, month: str, delta: int = 1) -> int:
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute("""
                INSERT INTO usage(device_id, month, messages_used)
                VALUES(%s, %s, %s)
                ON CONFLICT(device_id, month)
                DO UPDATE SET messages_used = usage.messages_used + %s
                RETURNING messages_used
            """, (device_id, month, delta, delta))

            new_val = cur.fetchone()[0]
        con.commit()
        return int(new_val)

init_db()

class ChatIn(BaseModel):
    device_id: str = Field(..., description="ID stabil per dispozitiv (UUID generat în aplicație)")
    text: str = Field(..., min_length=1, max_length=4000)

class ChatOut(BaseModel):
    blocked: bool
    messages_used: int
    limit: int
    reply: str

def mock_ifs_reply(user_text: str) -> str:
    t = user_text.lower()
    if any(k in t for k in ["trebuie", "control", "perfec", "disciplin"]):
        return ("Parcă e activă o parte care vrea să controleze sau să te țină „pe linie”. "
                "Cum e pentru tine să o observi ca pe o parte, nu ca pe tot tu? "
                "Unde o simți în corp?")
    if any(k in t for k in ["panic", "nu mai pot", "mă sufoc", "prea mult"]):
        return ("Sună ca o parte copleșită care vrea să scape repede de disconfort. "
                "Putem încetini puțin: ce ar avea nevoie acum ca să se simtă cu 5% mai în siguranță?")
    if any(k in t for k in ["vinovat", "rușine", "nu sunt bun", "inutil"]):
        return ("Aud rușine/vinovăție. Uneori apare și un critic care încearcă să prevină respingerea. "
                "Dacă îi dai un nume acestei părți, cum ai numi-o? "
                "Ce vrea să obțină pentru tine?")
    return ("Mulțumesc. Dacă privim prin lentila IFS: ce parte din tine e cea mai activă acum? "
            "Ce încearcă ea să facă pentru tine, chiar dacă metoda ei nu e plăcută?")

@app.get("/health")
def health():
    return {"ok": True}

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

@app.post("/chat", response_model=ChatOut, dependencies=[Depends(verify_api_key)])
def chat(payload: ChatIn):
    m = month_key()
    used = get_used(payload.device_id, m)

    if used >= MONTHLY_LIMIT:
        return ChatOut(blocked=True, messages_used=used, limit=MONTHLY_LIMIT, reply=LIMIT_MESSAGE)

    new_used = inc_used(payload.device_id, m, 1)
    reply = mock_ifs_reply(payload.text)
    return ChatOut(blocked=False, messages_used=new_used, limit=MONTHLY_LIMIT, reply=reply)
