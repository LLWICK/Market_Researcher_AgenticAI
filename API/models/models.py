from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Any
from datetime import datetime

class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class QueryRequest(BaseModel):
    query: str

class ChatHistory(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    query: str
    response: Any  # could be dict, list, or string depending on your agent pipeline
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        # allow MongoDB's `_id` field to map to Pydantic `id`
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
