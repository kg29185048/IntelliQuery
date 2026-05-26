from fastapi import APIRouter, HTTPException
import bcrypt
import os
from datetime import datetime, timedelta
@@ -40,7 +40,7 @@ def get_safe_password(pwd: str) -> bytes:


@router.post("/send-signup-otp")
async def send_signup_otp(data: SendSignupOtp):
    """Generates and sends an OTP for new user registration."""
    # Check if user already exists
    if users_collection.find_one({"email": data.email}):
@@ -58,17 +58,14 @@ async def send_signup_otp(data: SendSignupOtp):
        upsert=True
    )

    # Send email
    try:
        send_otp_email(to_email=data.email, otp=otp, is_reset=False)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to send OTP email")

    return {"message": "OTP sent successfully"}


@router.post("/signup")
async def signup(data: SignupVerify):
    """Verifies OTP and creates the new user."""
    # Check if user already exists
    if users_collection.find_one({"email": data.email}):
@@ -116,7 +113,7 @@ async def signup(data: SignupVerify):


@router.post("/login")
async def login(user: UserLogin):
    existing_user = users_collection.find_one({"email": user.email})

    if not existing_user:
@@ -153,7 +150,7 @@ async def login(user: UserLogin):


@router.post("/forgot-password")
async def forgot_password(data: ForgotPassword):
    """Generates and sends an OTP for password reset."""
    existing_user = users_collection.find_one({"email": data.email})
    if not existing_user:
@@ -173,17 +170,14 @@ async def forgot_password(data: ForgotPassword):
        upsert=True
    )

    # Send email
    try:
        send_otp_email(to_email=data.email, otp=otp, is_reset=True)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to send OTP email")

    return {"message": "If that email is registered, an OTP has been sent."}


@router.post("/reset-password")
async def reset_password(data: ResetPassword):
    """Verifies OTP and resets the password."""
    # Verify OTP
    otp_record = otps_collection.find_one({
@@ -217,7 +211,7 @@ async def reset_password(data: ResetPassword):


@router.post("/google")
async def google_auth(request: GoogleLoginRequest):
    """Verifies Google JWT token and logs in or registers the user."""
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
@@ -267,4 +261,4 @@ async def google_auth(request: GoogleLoginRequest):

    except ValueError:
        # Invalid token
        raise HTTPException(status_code=401, detail="Invalid Google token")
