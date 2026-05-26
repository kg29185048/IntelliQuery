from fastapi import APIRouter, HTTPException, BackgroundTasks
import bcrypt
import os
from datetime import datetime, timedelta
import random
from google.oauth2 import id_token
from google.auth.transport import requests

from api.models.user import (
    UserCreate, UserLogin, SendSignupOtp, SignupVerify, 
    ForgotPassword, ResetPassword, GoogleLoginRequest
)
from api.utils.jwt_handler import create_access_token
from api.utils.email_sender import send_otp_email
from database.mongo_client import get_db

router = APIRouter()

db = get_db()
users_collection = db["users"]
otps_collection = db["otps"]

# Create TTL index on otps collection (expires after 600 seconds = 10 minutes)
# Note: In a production app, index creation should be handled in a startup script, 
# but this ensures it exists.
try:
    otps_collection.create_index("createdAt", expireAfterSeconds=600)
except Exception:
    pass

def generate_otp() -> str:
    return str(random.randint(100000, 999999))

def get_safe_password(pwd: str) -> bytes:
    """
    Bcrypt has a strict 72-byte limit and requires bytes. 
    This encodes the string and safely truncates to strictly <= 72 bytes.
    """
    return pwd.encode('utf-8')[:72]


@router.post("/send-signup-otp")
def send_signup_otp(data: SendSignupOtp, background_tasks: BackgroundTasks):
    """Generates and sends an OTP for new user registration."""
    # Check if user already exists
    if users_collection.find_one({"email": data.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
        
    otp = generate_otp()
    
    # Store OTP in database (upsert to handle resends)
    otps_collection.update_one(
        {"email": data.email, "type": "signup"},
        {"$set": {
            "otp": otp, 
            "createdAt": datetime.utcnow()
        }},
        upsert=True
    )
    
    # Send email in background
    background_tasks.add_task(send_otp_email, to_email=data.email, otp=otp, is_reset=False)
        
    return {"message": "OTP sent successfully"}


@router.post("/signup")
def signup(data: SignupVerify):
    """Verifies OTP and creates the new user."""
    # Check if user already exists
    if users_collection.find_one({"email": data.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
        
    # Verify OTP
    otp_record = otps_collection.find_one({
        "email": data.email, 
        "type": "signup",
        "otp": data.otp
    })
    
    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        
    # OTP is valid, proceed with user creation
    # Bcrypt has a 72 byte limit. We truncate strictly by bytes.
    safe_password = get_safe_password(data.password)
    hashed_password = bcrypt.hashpw(safe_password, bcrypt.gensalt()).decode('utf-8')

    new_user = {
        "name": data.name,
        "email": data.email,
        "password": hashed_password
    }

    result = users_collection.insert_one(new_user)
    
    # Clean up OTP
    otps_collection.delete_one({"_id": otp_record["_id"]})

    token = create_access_token({
        "user_id": str(result.inserted_id),
        "email": data.email
    })

    return {
        "token": token,
        "user": {
            "id": str(result.inserted_id),
            "name": data.name,
            "email": data.email
        }
    }


@router.post("/login")
def login(user: UserLogin):
    existing_user = users_collection.find_one({"email": user.email})

    if not existing_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Check if legacy plain text password or hashed password
    stored_password = existing_user["password"]
    is_valid = False
    
    # Simple check: bcrypt hashes start with $2
    safe_password = get_safe_password(user.password)
    if stored_password.startswith("$2"):
        is_valid = bcrypt.checkpw(safe_password, stored_password.encode('utf-8'))
    else:
        # Legacy plain text verification
        is_valid = (stored_password == user.password)

    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "user_id": str(existing_user["_id"]),
        "email": existing_user["email"]
    })

    return {
        "token": token,
        "user": {
            "id": str(existing_user["_id"]),
            "name": existing_user["name"],
            "email": existing_user["email"]
        }
    }


@router.post("/forgot-password")
def forgot_password(data: ForgotPassword, background_tasks: BackgroundTasks):
    """Generates and sends an OTP for password reset."""
    existing_user = users_collection.find_one({"email": data.email})
    if not existing_user:
        # For security reasons, don't reveal if email exists, but we can't send an email
        # Returning success prevents email enumeration
        return {"message": "If that email is registered, an OTP has been sent."}
        
    otp = generate_otp()
    
    # Store OTP in database (upsert to handle resends)
    otps_collection.update_one(
        {"email": data.email, "type": "reset"},
        {"$set": {
            "otp": otp, 
            "createdAt": datetime.utcnow()
        }},
        upsert=True
    )
    
    # Send email in background
    background_tasks.add_task(send_otp_email, to_email=data.email, otp=otp, is_reset=True)
        
    return {"message": "If that email is registered, an OTP has been sent."}


@router.post("/reset-password")
def reset_password(data: ResetPassword):
    """Verifies OTP and resets the password."""
    # Verify OTP
    otp_record = otps_collection.find_one({
        "email": data.email, 
        "type": "reset",
        "otp": data.otp
    })
    
    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        
    # Check user exists
    existing_user = users_collection.find_one({"email": data.email})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Hash new password (truncate to 72 bytes to prevent bcrypt length error)
    safe_password = get_safe_password(data.new_password)
    hashed_password = bcrypt.hashpw(safe_password, bcrypt.gensalt()).decode('utf-8')
    
    # Update password
    users_collection.update_one(
        {"email": data.email},
        {"$set": {"password": hashed_password}}
    )
    
    # Clean up OTP
    otps_collection.delete_many({"email": data.email, "type": "reset"})
    
    return {"message": "Password reset successfully"}


@router.post("/google")
def google_auth(request: GoogleLoginRequest):
    """Verifies Google JWT token and logs in or registers the user."""
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=500, detail="Google Login is not configured on the server.")

    try:
        # Verify the token
        idinfo = id_token.verify_oauth2_token(request.token, requests.Request(), client_id)
        
        email = idinfo.get("email")
        name = idinfo.get("name", "Google User")

        if not email:
            raise HTTPException(status_code=400, detail="Google token missing email")

        # Check if user exists
        existing_user = users_collection.find_one({"email": email})
        
        if existing_user:
            user_id = str(existing_user["_id"])
        else:
            # Register new user automatically
            # We don't have a password for Google users, so we can set a random impossible hash or flag
            # Bcrypt hashes are exactly 60 chars. We can just set password to "OAUTH_USER" to fail regular logins
            new_user = {
                "name": name,
                "email": email,
                "password": "OAUTH_USER" 
            }
            result = users_collection.insert_one(new_user)
            user_id = str(result.inserted_id)

        # Generate JWT
        token = create_access_token({
            "user_id": user_id,
            "email": email
        })

        return {
            "token": token,
            "user": {
                "id": user_id,
                "name": name,
                "email": email
            }
        }

    except ValueError:
        # Invalid token
        raise HTTPException(status_code=401, detail="Invalid Google token")
