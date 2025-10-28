from pydantic import BaseModel


class TokenResponse(BaseModel):
    token_type: str
    access_token: str
