from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from app.auth import authenticate_user, create_access_token, get_current_user, get_current_user_with_roles

class SwitchRoleRequest(BaseModel):
    company_id: str = "system"
    role_id: str

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user["email"]})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me")
async def read_users_me(current_user=Depends(get_current_user)):
    return {"user": current_user}


@router.get("/me/with-roles")
async def read_users_me_with_roles(current_user=Depends(get_current_user_with_roles)):
    return {"user": current_user}


@router.get("/debug/repo-state")  
async def debug_repo_state():
    """Check repo state from within server"""
    from app.repo import repo
    result = {
        "repo_type": type(repo).__name__,
        "has_store": hasattr(repo, '_store')
    }
    
    if hasattr(repo, '_store'):
        result["store_keys"] = list(repo._store.keys())
        result["users_count"] = len(repo._store.get("__users__", {}))
        
        # Show user details
        users = repo._store.get("__users__", {})
        result["users"] = [{"id": uid, "email": user.get("email")} for uid, user in users.items()]
    
    return result


@router.post("/admin/force-init")
async def force_initialize_data():
    """Force initialize data from within server context"""
    try:
        from app.auth import init_default_data
        from app.repo import repo
        
        # Show before state
        before_users = len(repo._store.get("__users__", {})) if hasattr(repo, '_store') else 0
        
        # Clear and initialize
        if hasattr(repo, '_store'):
            repo._store.clear()
        
        await init_default_data()
        
        # Show after state
        if hasattr(repo, '_store'):
            users = repo._store.get("__users__", {})
            user_list = [{"id": uid, "email": user.get("email")} for uid, user in users.items()]
            
            return {
                "success": True,
                "message": "Data force initialized",
                "before_users": before_users,
                "after_users": len(users),
                "users": user_list
            }
        else:
            return {"success": True, "message": "MongoDB data initialized"}
            
    except Exception as e:
        import traceback
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}



@router.post("/switch-role")
async def switch_user_role(
    request: dict = Body(...),
    current_user=Depends(get_current_user_with_roles)
):
    """Switch user's active role and company"""
    company_id = request.get("company_id")
    role_id = request.get("role_id")
    
    if not company_id or not role_id:
        raise HTTPException(status_code=400, detail="company_id and role_id are required")
    
    user_roles = current_user.get("roles", [])

    # Find the role that matches the requested company and role_id
    selected_role = None
    for user_role in user_roles:
        if user_role["company_id"] == company_id and user_role["role_id"] == role_id:
            selected_role = user_role
            break

    if not selected_role:
        raise HTTPException(status_code=400, detail="Invalid role or company selection")

    # Update the user's default role (you might want to store this in the database)
    current_user["active_company"] = company_id
    current_user["active_role"] = role_id

    return {"message": "Role switched successfully", "user": current_user}
