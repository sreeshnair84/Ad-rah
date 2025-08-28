from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from app.auth import authenticate_user, create_access_token, get_current_user, get_current_user_with_roles

class SwitchRoleRequest(BaseModel):
    company_id: str
    role: str

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



class SwitchRoleRequest(BaseModel):
    company_id: str = "system"
    role_id: str

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
