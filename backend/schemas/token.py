# filepath: D:\Replit Web App\text2sql-app\backend\schemas\token.py
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None 
