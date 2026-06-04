from pydantic import BaseModel, Field


class ChatIn(BaseModel):
    device_id: str = Field(..., description="ID stabil per dispozitiv (UUID generat în aplicație)")
    text: str = Field(..., min_length=1, max_length=4000)


class ChatOut(BaseModel):
    blocked: bool
    messages_used: int
    limit: int
    reply: str

class MessageOut(BaseModel):
    role: str
    text: str
    created_at: str