from pydantic import BaseModel, EmailStr
from typing import Optional


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserInDB(BaseModel):
    id: Optional[str] = None
    name: str
    email: EmailStr
    password_hash: str


class SendSignupOtp(BaseModel):
    name: str
    email: EmailStr
    password: str


class SignupVerify(BaseModel):
    name: str
    email: EmailStr
    password: str
    otp: str


class ForgotPassword(BaseModel):
    email: EmailStr


class ResetPassword(BaseModel):
    email: EmailStr
    otp: str
    new_password: str


class GoogleLoginRequest(BaseModel):
    token: str