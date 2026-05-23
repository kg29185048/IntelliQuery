from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import string
import random
from bson import ObjectId

from database.mongo_client import get_db
from api.dependencies import get_current_user
from api.utils.encryption import encrypt_uri, decrypt_uri

router = APIRouter()

# Pydantic models for request/response
class WorkspaceCreate(BaseModel):
    name: str
    db_type: str
    db_uri: str
    db_name: Optional[str] = None

class WorkspaceJoin(BaseModel):
    join_code: str

class MemberUpdate(BaseModel):
    permission: str # "read_only" or "read_write"

def generate_join_code(length=6):
    """Generate a random alphanumeric join code"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

@router.post("/")
async def create_workspace(workspace: WorkspaceCreate, current_user: dict = Depends(get_current_user)):
    db = get_db()
    
    # Generate unique join code
    while True:
        code = generate_join_code()
        if not db["workspaces"].find_one({"join_code": code}):
            break
            
    workspace_data = {
        "name": workspace.name,
        "admin_id": current_user["id"],
        "db_type": workspace.db_type,
        "db_uri": encrypt_uri(workspace.db_uri),
        "db_name": workspace.db_name,
        "join_code": code,
        "created_at": datetime.utcnow()
    }
    
    result = db["workspaces"].insert_one(workspace_data)
    workspace_id = str(result.inserted_id)
    
    # Add creator as admin member
    member_data = {
        "workspace_id": workspace_id,
        "user_id": current_user["id"],
        "role": "admin",
        "permission": "read_write",
        "joined_at": datetime.utcnow()
    }
    db["workspace_members"].insert_one(member_data)
    
    return {
        "id": workspace_id,
        "name": workspace.name,
        "join_code": code,
        "role": "admin",
        "permission": "read_write"
    }

@router.get("/")
async def list_workspaces(current_user: dict = Depends(get_current_user)):
    db = get_db()
    
    # Find all memberships for current user
    memberships = list(db["workspace_members"].find({"user_id": current_user["id"]}))
    if not memberships:
        return []
        
    workspace_ids = [ObjectId(m["workspace_id"]) for m in memberships]
    workspaces = list(db["workspaces"].find({"_id": {"$in": workspace_ids}}))
    
    result = []
    for ws in workspaces:
        # Find matching membership to get role/permission
        member = next((m for m in memberships if m["workspace_id"] == str(ws["_id"])), None)
        if member:
            result.append({
                "id": str(ws["_id"]),
                "name": ws["name"],
                "join_code": ws["join_code"] if member["role"] == "admin" else None,
                "role": member["role"],
                "permission": member["permission"],
                "db_type": ws["db_type"],
                "created_at": ws.get("created_at")
            })
            
    return result

@router.post("/join")
async def join_workspace(join_data: WorkspaceJoin, current_user: dict = Depends(get_current_user)):
    db = get_db()
    
    workspace = db["workspaces"].find_one({"join_code": join_data.join_code.upper()})
    if not workspace:
        raise HTTPException(status_code=404, detail="Invalid join code")
        
    workspace_id = str(workspace["_id"])
    
    # Check if already a member
    existing = db["workspace_members"].find_one({
        "workspace_id": workspace_id,
        "user_id": current_user["id"]
    })
    
    if existing:
        return {
            "id": workspace_id,
            "name": workspace["name"],
            "role": existing["role"],
            "permission": existing["permission"],
            "db_type": workspace["db_type"]
        }
        
    # Add user as read_only member
    member_data = {
        "workspace_id": workspace_id,
        "user_id": current_user["id"],
        "role": "user",
        "permission": "read_only",
        "joined_at": datetime.utcnow()
    }
    db["workspace_members"].insert_one(member_data)
    
    return {
        "id": workspace_id,
        "name": workspace["name"],
        "role": "user",
        "permission": "read_only",
        "db_type": workspace["db_type"]
    }

@router.get("/{workspace_id}/members")
async def get_workspace_members(workspace_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    
    # Verify current user is admin of this workspace
    membership = db["workspace_members"].find_one({
        "workspace_id": workspace_id,
        "user_id": current_user["id"]
    })
    
    if not membership or membership["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view members")
        
    members = list(db["workspace_members"].find({"workspace_id": workspace_id}))
    
    # Get user details for these members
    user_ids = [ObjectId(m["user_id"]) for m in members]
    users = list(db["users"].find({"_id": {"$in": user_ids}}))
    
    result = []
    for member in members:
        user = next((u for u in users if str(u["_id"]) == member["user_id"]), None)
        if user:
            result.append({
                "user_id": member["user_id"],
                "name": user.get("name", "Unknown"),
                "email": user.get("email", ""),
                "role": member["role"],
                "permission": member["permission"],
                "joined_at": member.get("joined_at")
            })
            
    return result

@router.put("/{workspace_id}/members/{user_id}")
async def update_member_permission(
    workspace_id: str, 
    user_id: str, 
    update_data: MemberUpdate, 
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    
    if update_data.permission not in ["read_only", "read_write"]:
        raise HTTPException(status_code=400, detail="Invalid permission level")
        
    # Verify current user is admin
    membership = db["workspace_members"].find_one({
        "workspace_id": workspace_id,
        "user_id": current_user["id"]
    })
    
    if not membership or membership["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can modify permissions")
        
    # Cannot change own permissions this way
    if current_user["id"] == user_id:
        raise HTTPException(status_code=400, detail="Cannot modify your own permissions")
        
    # Update member
    result = db["workspace_members"].update_one(
        {"workspace_id": workspace_id, "user_id": user_id},
        {"$set": {"permission": update_data.permission}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Member not found in this workspace")
        
    return {"status": "success", "message": "Permissions updated"}

@router.delete("/{workspace_id}")
async def delete_workspace(workspace_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    
    # Verify current user is admin of this workspace
    membership = db["workspace_members"].find_one({
        "workspace_id": workspace_id,
        "user_id": current_user["id"]
    })
    
    if not membership or membership["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete the workspace")
        
    # Delete the workspace
    result = db["workspaces"].delete_one({"_id": ObjectId(workspace_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    # Delete all members associated with this workspace
    db["workspace_members"].delete_many({"workspace_id": workspace_id})
    
    return {"status": "success", "message": "Workspace deleted successfully"}

        
@router.delete("/{workspace_id}/members/{user_id}")
async def remove_member(
    workspace_id: str, 
    user_id: str, 
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    
    is_self = (current_user["id"] == user_id)
    
    # Verify current user is an admin if they are removing someone else
    if not is_self:
        current_membership = db["workspace_members"].find_one({
            "workspace_id": workspace_id,
            "user_id": current_user["id"]
        })
        if not current_membership or current_membership["role"] != "admin":
            raise HTTPException(status_code=403, detail="Only admins can remove other members")
            
    # Check if the target user is a member
    target_membership = db["workspace_members"].find_one({
        "workspace_id": workspace_id,
        "user_id": user_id
    })
    
    if not target_membership:
        raise HTTPException(status_code=404, detail="Member not found in this workspace")
        
    # If the target is an admin, ensure they are not the last admin
    if target_membership["role"] == "admin":
        admin_count = db["workspace_members"].count_documents({
            "workspace_id": workspace_id,
            "role": "admin"
        })
        if admin_count <= 1:
            raise HTTPException(
                status_code=400, 
                detail="Cannot remove the last admin of the workspace. Please assign another admin or delete the workspace."
            )
            
    db["workspace_members"].delete_one({
        "workspace_id": workspace_id,
        "user_id": user_id
    })
    
    message = "You have left the workspace" if is_self else "Member removed successfully"
    return {"status": "success", "message": message}


