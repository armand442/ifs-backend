from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL


client = OpenAI(api_key=OPENAI_API_KEY)


SYSTEM_PROMPT = """
Ești un asistent conversațional de suport psihoterapeutic în stil IFS.
Nu ești terapeut și nu pui diagnostice.
Răspunzi calm, empatic, scurt și clar.
Ajuți utilizatorul să observe părți interne, emoții, senzații corporale și nevoi.
Nu forțezi introspecția.
Nu judeci.
Nu dai sfaturi medicale.
Dacă apar indicii de auto-vătămare, suicid sau pericol imediat, recomanzi contactarea serviciilor de urgență sau a unei persoane de încredere.
"""


def build_openai_messages(context: list[dict], current_text: str):
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    for item in context:
        role = item.get("role")
        text = item.get("text")

        if role in ["user", "assistant"] and text:
            messages.append({
                "role": role,
                "content": text
            })

    messages.append({
        "role": "user",
        "content": current_text
    })

    return messages


def generate_ai_reply(context: list[dict], current_text: str) -> str:
    if not OPENAI_API_KEY:
        raise Exception("OPENAI_API_KEY is not configured")

    messages = build_openai_messages(context, current_text)

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=250,
    )

    return response.choices[0].message.content.strip()