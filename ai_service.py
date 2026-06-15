from dataclasses import dataclass

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


@dataclass
class AIReplyResult:
    reply: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    input_cost_usd: float
    output_cost_usd: float
    total_cost_usd: float


# Valori pentru gpt-4o-mini.
# Le ținem aici temporar; pasul următor va fi să le mutăm în config/env.
INPUT_COST_PER_1M_TOKENS = 0.15
OUTPUT_COST_PER_1M_TOKENS = 0.60


def calculate_cost(input_tokens: int, output_tokens: int):
    input_cost = (input_tokens / 1_000_000) * INPUT_COST_PER_1M_TOKENS
    output_cost = (output_tokens / 1_000_000) * OUTPUT_COST_PER_1M_TOKENS
    total_cost = input_cost + output_cost

    return input_cost, output_cost, total_cost


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


def generate_ai_reply(context: list[dict], current_text: str) -> AIReplyResult:
    if not OPENAI_API_KEY:
        raise Exception("OPENAI_API_KEY is not configured")

    messages = build_openai_messages(context, current_text)

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=250,
    )

    reply = response.choices[0].message.content.strip()

    usage = response.usage
    input_tokens = usage.prompt_tokens if usage else 0
    output_tokens = usage.completion_tokens if usage else 0
    total_tokens = usage.total_tokens if usage else input_tokens + output_tokens

    input_cost, output_cost, total_cost = calculate_cost(input_tokens, output_tokens)

    return AIReplyResult(
        reply=reply,
        model=OPENAI_MODEL,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        input_cost_usd=input_cost,
        output_cost_usd=output_cost,
        total_cost_usd=total_cost
    )