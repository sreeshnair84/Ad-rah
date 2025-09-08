from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
import secrets
import hashlib
from app.models import UserRegistration, UserInvitation, PasswordResetRequest, PasswordReset, User
from app.repo import repo
from app.auth_service import get_current_user, require_roles, auth_service
from app.email_service import email_service, EmailSchema

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register_user(user_data: UserRegistration):
    """Register a new user without roles (for invited users)"""
    # Check if user already exists
    existing_user = await repo.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    # Check if there's a valid invitation
    invitations = await repo.get_user_invitations_by_email(user_data.email)
    valid_invitation = None
    for invitation in invitations:
        expires_at = invitation.get("expires_at")
        if (invitation.get("status") == "pending" and
            expires_at and
            datetime.fromisoformat(expires_at) > datetime.utcnow()):
            valid_invitation = invitation
            break

    if not valid_invitation:
        raise HTTPException(status_code=400, detail="No valid invitation found for this email")

    # Create user
    user_obj = User(
        name=user_data.name,
        email=user_data.email,
        phone=user_data.phone,
        hashed_password=auth_service.hash_password(user_data.password),
        status="active",
        email_verified=True
    )

    saved_user = await repo.save_user(user_obj)
    user_id = saved_user["id"]

    # Create user role from invitation
    from app.models import UserRole
    user_role = UserRole(
        user_id=user_id,
        company_id=valid_invitation["company_id"],
        role_id=valid_invitation["role_id"],
        is_default=True,
        status="active"
    )
    await repo.save_user_role(user_role)

    # Mark invitation as accepted
    await repo.update_user_invitation_status(valid_invitation["id"], "accepted")

    return {"message": "User registered successfully", "user_id": user_id}


@router.post("/invite-user")
async def invite_user(
    email: str,
    company_id: str,
    role_id: str,
    current_user=Depends(require_roles("ADMIN", "HOST"))
):
    """Invite a user to join (Admin or Host only)"""
    # Check if user already exists
    existing_user = await repo.get_user_by_email(email)
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    # Check if invitation already exists
    existing_invitations = await repo.get_user_invitations_by_email(email)
    for invitation in existing_invitations:
        if invitation.get("status") == "pending":
            raise HTTPException(status_code=400, detail="Invitation already sent to this email")

    # Generate invitation token
    invitation_token = secrets.token_urlsafe(32)

    # Get inviter info
    inviter_name = current_user.get("name", "Admin")
    company = await repo.get_company(company_id)
    company_name = company.get("name", "Company") if company else "Company"

    # Create invitation
    invitation = UserInvitation(
        email=email,
        invited_by=current_user["id"],
        company_id=company_id,
        role_id=role_id,
        invitation_token=invitation_token,
        expires_at=datetime.utcnow() + timedelta(days=7),
        status="pending"
    )

    await repo.save_user_invitation(invitation)

    # Send invitation email
    try:
        email_body = email_service.get_user_invitation_template(
            invitation_token,
            inviter_name,
            company_name
        )
        await email_service.send_email(EmailSchema(
            email=[email],
            subject="You're invited to join OpenKiosk",
            body=email_body
        ))
    except Exception as e:
        print(f"Failed to send invitation email: {e}")

    return {"message": "Invitation sent successfully"}


@router.post("/request-password-reset")
async def request_password_reset(request: PasswordResetRequest):
    """Request a password reset"""
    user = await repo.get_user_by_email(request.email)
    if not user:
        # Don't reveal if email exists or not
        return {"message": "If the email exists, a password reset link has been sent"}

    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)

    # Save reset token
    from app.models import PasswordResetToken
    reset_token_obj = PasswordResetToken(
        user_id=user["id"],
        reset_token=reset_token,
        expires_at=expires_at,
        used=False
    )
    await repo.save_password_reset_token(reset_token_obj)

    # Send reset email
    try:
        user_name = user.get("name", "User")
        email_body = email_service.get_password_reset_template(reset_token, user_name)
        await email_service.send_email(EmailSchema(
            email=[request.email],
            subject="Password Reset Request",
            body=email_body
        ))
    except Exception as e:
        print(f"Failed to send reset email: {e}")

    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password")
async def reset_password(reset_data: PasswordReset):
    """Reset password using token"""
    # Find valid reset token
    token_data = await repo.get_password_reset_token(reset_data.token)
    if not token_data:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    # Check if token is expired
    if datetime.fromisoformat(token_data["expires_at"]) < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Reset token has expired")

    # Update user password
    user = await repo.get_user(token_data["user_id"])
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    user["hashed_password"] = auth_service.hash_password(reset_data.new_password)
    from app.models import User
    user_obj = User(**user)
    await repo.save_user(user_obj)

    # Mark token as used
    await repo.mark_password_reset_token_used(token_data["id"])

    return {"message": "Password reset successfully"}


@router.get("/complete-registration")
async def complete_registration(token: str):
    """Verify invitation token for registration completion"""
    invitation = await repo.get_user_invitation_by_token(token)
    if not invitation:
        raise HTTPException(status_code=400, detail="Invalid invitation token")

    if invitation["status"] != "pending":
        raise HTTPException(status_code=400, detail="Invitation has already been used or expired")

    if datetime.fromisoformat(invitation["expires_at"]) < datetime.utcnow():
        await repo.update_user_invitation_status(invitation["id"], "expired")
        raise HTTPException(status_code=400, detail="Invitation has expired")

    return {
        "message": "Valid invitation",
        "email": invitation["email"],
        "company_id": invitation["company_id"],
        "role_id": invitation["role_id"]
    }
