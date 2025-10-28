from typing import Optional
from pydantic import BaseModel, constr, Field, EmailStr


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    country_code: int
    phone_number: int
    password: constr(min_length=8, max_length=128)


class UserBase(BaseModel):
    username: str
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: Optional[int] = Field(
        None, description="Phone number without +country code"
    )
    country_code: Optional[int] = Field(
        None, description="Country dialing code, e.g. 1 for USA"
    )
    is_premium: Optional[bool] = False
    ip_address: str


class UserUpdate(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[EmailStr]
    phone_number: Optional[int]
    country_code: Optional[int]
    is_premium: Optional[bool]


class UserResult(BaseModel):
    id: int
    model_config = {"from_attributes": True}
