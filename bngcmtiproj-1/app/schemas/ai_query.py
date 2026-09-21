from pydantic import BaseModel

class AIQueryIn(BaseModel):
    query: str

class AIQueryOut(BaseModel):
    success: bool
    question: str
    sql: str
    data: list
    answer: str
    error: str = None
