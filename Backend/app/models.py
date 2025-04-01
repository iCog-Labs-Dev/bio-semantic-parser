from pydantic import BaseModel

class UserRequest(BaseModel):
    query: str

class APIResponse(BaseModel):
    result: str
