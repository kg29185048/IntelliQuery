from fastapi import APIRouter, HTTPException
from api.models.user import UserCreate, UserLogin
from api.utils.jwt_handler import (
    create_access_token
)

from database.mongo_client import get_db

router = APIRouter()

db = get_db()

users_collection = db["users"]


@router.post("/signup")
async def signup(user: UserCreate):

    new_user = {
        "name": user.name,
        "email": user.email,
        "password": user.password
    }

    result = users_collection.insert_one(new_user)

    token = create_access_token({
        "user_id": str(result.inserted_id),
        "email": user.email
    })

    return {
        "token": token,
        "user": {
            "id": str(result.inserted_id),
            "name": user.name,
            "email": user.email
        }
    }


@router.post("/login")
async def login(user: UserLogin):

    existing_user = users_collection.find_one({
        "email": user.email
    })

    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    if existing_user["password"] != user.password:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

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