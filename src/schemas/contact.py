from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from datetime import date, datetime
from typing import Optional

from src.schemas.user import UserResponse


def validate_birthday(value: date) -> date:
    if value > date.today():
        raise ValueError(
            'The date of birth cannot be greater than the current one.')
    return value


def validate_phone_number(value: str) -> str:
    if not (value.isdigit() and len(value) == 10):
        raise ValueError('Phone number must contain exactly 10 digits')
    return value


class ContactBase(BaseModel):
    first_name: str = Field(min_length=3, max_length=20)
    last_name: str = Field(min_length=3, max_length=20)
    email: EmailStr
    phone_number: str
    birthday: date
    additional_info: Optional[str] = None

    @field_validator('phone_number')
    def validate_phone_number(cls, value):
        return validate_phone_number(value)

    @field_validator('birthday')
    def validate_birthday(cls, value):
        return validate_birthday(value)


class ContactCreateSchema(ContactBase):
    pass


class ContactUpdateSchema(BaseModel):
    first_name: Optional[str] = Field(None, min_length=3, max_length=20)
    last_name: Optional[str] = Field(None, min_length=3, max_length=20)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    birthday: Optional[date] = None
    additional_info: Optional[str] = None

    @field_validator('phone_number')
    def validate_phone_number(cls, value):
        return validate_phone_number(value)

    @field_validator('birthday')
    def validate_birthday(cls, value):
        return validate_birthday(value)


class ContactResponse(ContactBase):
    id: int
    created_at: datetime | None
    updated_at: datetime | None
    # user: UserResponse | None


class ContactShortResponse(BaseModel):
    first_name: str
    last_name: str
    birthday: date
    created_at: datetime | None
    updated_at: datetime | None
    # user: UserResponse | None
    
    model_config = ConfigDict(from_attributes = True)   
