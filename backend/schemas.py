
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str

class GoogleAuthRequest(BaseModel):
    token: str

class MicrosoftAuthRequest(BaseModel):
    code: str
