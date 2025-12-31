from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    email: str
    password: str

class Task(BaseModel):
    title: str
    completed: bool = False
    user_email: str
