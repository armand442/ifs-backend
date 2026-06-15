from database import get_connection


LIMIT_MESSAGE = (
    "Ai ajuns la limita de mesaje disponibile pentru această perioadă. "
    "Poți activa un plan extins pentru a continua sau poți nota ce apare și aduce în ședință."
)


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


def save_chat_message(device_id: str, role: str, text: str):
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute("""
                INSERT INTO chat_messages(device_id, role, text)
                VALUES(%s, %s, %s)
            """, (device_id, role, text))

        con.commit()

def save_ai_usage_log(
    device_id: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    total_tokens: int,
    input_cost_usd: float,
    output_cost_usd: float,
    total_cost_usd: float,
    success: bool = True,
    error_message: str | None = None,
):
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute("""
                INSERT INTO ai_usage_logs(
                    device_id,
                    model,
                    input_tokens,
                    output_tokens,
                    total_tokens,
                    input_cost_usd,
                    output_cost_usd,
                    total_cost_usd,
                    success,
                    error_message
                )
                VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                device_id,
                model,
                input_tokens,
                output_tokens,
                total_tokens,
                input_cost_usd,
                output_cost_usd,
                total_cost_usd,
                success,
                error_message
            ))

        con.commit()


def get_recent_messages(device_id: str, limit: int = 20):
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute("""
                SELECT role, text, created_at
                FROM chat_messages
                WHERE device_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (device_id, limit))

            rows = cur.fetchall()

    messages = [
        {
            "role": row[0],
            "text": row[1],
            "created_at": row[2].isoformat()
        }
        for row in rows
    ]

    return list(reversed(messages))
def get_conversation_context(device_id: str, limit: int = 10):
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute("""
                SELECT role, text
                FROM chat_messages
                WHERE device_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (device_id, limit))

            rows = cur.fetchall()

    messages = [
        {
            "role": row[0],
            "text": row[1]
        }
        for row in reversed(rows)
    ]

    return messages


def mock_ifs_reply(user_text: str) -> str:
    t = user_text.lower()

    if any(k in t for k in ["trebuie", "control", "perfec", "disciplin"]):
        return (
            "Parcă e activă o parte care vrea să controleze sau să te țină „pe linie”. "
            "Cum e pentru tine să o observi ca pe o parte, nu ca pe tot tu? "
            "Unde o simți în corp?"
        )

    if any(k in t for k in ["panic", "nu mai pot", "mă sufoc", "prea mult"]):
        return (
            "Sună ca o parte copleșită care vrea să scape repede de disconfort. "
            "Putem încetini puțin: ce ar avea nevoie acum ca să se simtă cu 5% mai în siguranță?"
        )

    if any(k in t for k in ["vinovat", "rușine", "nu sunt bun", "inutil"]):
        return (
            "Aud rușine/vinovăție. Uneori apare și un critic care încearcă să prevină respingerea. "
            "Dacă îi dai un nume acestei părți, cum ai numi-o? "
            "Ce vrea să obțină pentru tine?"
        )

    return (
        "Mulțumesc. Dacă privim prin lentila IFS: ce parte din tine e cea mai activă acum? "
        "Ce încearcă ea să facă pentru tine, chiar dacă metoda ei nu e plăcută?"
    )
def delete_old_chat_messages(hours: int = 24) -> int:
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute("""
                DELETE FROM chat_messages
                WHERE created_at < NOW() - (%s || ' hours')::INTERVAL
                RETURNING id
            """, (hours,))

            deleted_rows = cur.fetchall()

        con.commit()
        return len(deleted_rows) 


CRISIS_MESSAGE = (
    "Îmi pare rău că treci prin asta. Dacă simți că ai putea să-ți faci rău "
    "sau ești în pericol imediat, te rog sună acum la 112 sau mergi la cea mai apropiată cameră de gardă. "
    "Dacă poți, spune unei persoane de încredere unde ești și că ai nevoie de ajutor chiar acum."
)


def detect_crisis_risk(text: str) -> bool:
    t = text.lower()

    crisis_keywords = [
        "vreau să mor",
        "vreau sa mor",
        "mă omor",
        "ma omor",
        "sinucidere",
        "suicid",
        "nu mai vreau să trăiesc",
        "nu mai vreau sa traiesc",
        "îmi fac rău",
        "imi fac rau",
        "vreau să-mi fac rău",
        "vreau sa-mi fac rau",
    ]

    return any(keyword in t for keyword in crisis_keywords)