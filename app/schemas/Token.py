from pydantic import BaseModel


class Token(BaseModel):
    token_type: str
    token: str