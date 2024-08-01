from pydantic import BaseModel, EmailStr


class EmailValidator(BaseModel):
    email: EmailStr
