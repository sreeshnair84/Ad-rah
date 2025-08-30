from typing import Optional, Dict, List
import asyncio
import logging
from datetime import datetime
from app.models import ContentMetadata, ContentMeta, Company, User, UserRole, Role, RolePermission, UserProfile, UserInvitation, PasswordResetToken, CompanyApplication, CompanyApplicationStatus
from app.config import settings

logger = logging.getLogger(__name__)

# Try to import ObjectId for MongoDB operations
try:
    from bson import ObjectId
    _OBJECTID_AVAILABLE = True
except ImportError:
    ObjectId = None
    _OBJECTID_AVAILABLE = False

# If MONGO_URI is set we will use motor; else use a simple in-memory store for dev/test
if getattr(settings, "MONGO_URI", None):
    try:
        import motor.motor_asyncio as motor
        _MONGO_AVAILABLE = True
    except Exception:
        motor = None
        _MONGO_AVAILABLE = False
else:
    motor = None
    _MONGO_AVAILABLE = False


class InMemoryRepo:
    def __init__(self):
        self._store: Dict[str, dict] = {}
        self._lock = asyncio.Lock()

    async def save(self, meta: ContentMetadata) -> dict:
        async with self._lock:
            meta.id = meta.id or str(len(self._store) + 1)
            self._store[meta.id] = meta.model_dump(exclude_none=True)
            return self._store[meta.id]

    async def get(self, _id: str) -> Optional[dict]:
        return self._store.get(_id)

    async def list(self) -> List[Dict]:
        return list(self._store.values())

    # ContentMeta operations
    async def save_content_meta(self, meta: ContentMeta) -> dict:
        async with self._lock:
            content_meta = self._store.setdefault("__content_meta__", {})
            meta.id = meta.id or str(len(content_meta) + 1) + "-cm"
            content_meta[meta.id] = meta.model_dump(exclude_none=True)
            return content_meta[meta.id]

    async def get_content_meta(self, _id: str) -> Optional[dict]:
        return self._store.get("__content_meta__", {}).get(_id)

    async def list_content_meta(self) -> List[Dict]:
        return list(self._store.get("__content_meta__", {}).values())

    # Role operations
    async def save_role(self, role: Role) -> dict:
        async with self._lock:
            roles = self._store.setdefault("__roles__", {})
            role.id = role.id or str(len(roles) + 1) + "-r"
            roles[role.id] = role.model_dump(exclude_none=True)
            return roles[role.id]

    async def get_role(self, _id: str) -> Optional[dict]:
        return self._store.get("__roles__", {}).get(_id)

    async def list_roles_by_company(self, company_id: str) -> List[Dict]:
        roles = self._store.get("__roles__", {})
        return [role for role in roles.values() if role.get("company_id") == company_id]

    async def list_roles_by_group(self, role_group: str) -> List[Dict]:
        roles = self._store.get("__roles__", {})
        return [role for role in roles.values() if role.get("role_group") == role_group]

    async def get_default_roles_by_company(self, company_id: str) -> List[Dict]:
        roles = self._store.get("__roles__", {})
        return [role for role in roles.values()
                if role.get("company_id") == company_id and role.get("is_default", False)]

    async def delete_role(self, _id: str) -> bool:
        async with self._lock:
            if _id in self._store.get("__roles__", {}):
                del self._store["__roles__"][_id]
                return True
            return False

    # RolePermission operations
    async def save_role_permission(self, permission: RolePermission) -> dict:
        async with self._lock:
            role_perms = self._store.setdefault("__role_permissions__", {})
            permission.id = permission.id or str(len(role_perms) + 1) + "-rp"
            role_perms[permission.id] = permission.model_dump(exclude_none=True)
            return role_perms[permission.id]

    async def get_role_permissions(self, role_id: str) -> List[Dict]:
        permissions = self._store.get("__role_permissions__", {})
        return [p for p in permissions.values() if p.get("role_id") == role_id]

    # moderation related
    async def save_review(self, review: dict) -> dict:
        async with self._lock:
            reviews = self._store.setdefault("__reviews__", {})
            rid = review.get("id") or str(len(reviews) + 1) + "-rev"
            review["id"] = rid
            reviews[rid] = review
            return review

    async def list_reviews(self) -> List[Dict]:
        return list(self._store.get("__reviews__", {}).values())

    # Company operations
    async def save_company(self, company: Company) -> dict:
        async with self._lock:
            companies = self._store.setdefault("__companies__", {})
            company.id = company.id or str(len(companies) + 1) + "-c"
            companies[company.id] = company.model_dump(exclude_none=True)
            return companies[company.id]

    async def get_company(self, _id: str) -> Optional[dict]:
        return self._store.get("__companies__", {}).get(_id)

    async def list_companies(self) -> List[Dict]:
        return list(self._store.get("__companies__", {}).values())

    async def delete_company(self, _id: str) -> bool:
        async with self._lock:
            if _id in self._store.get("__companies__", {}):
                del self._store["__companies__"][_id]
                return True
            return False

    # User operations
    async def save_user(self, user: User) -> dict:
        async with self._lock:
            users = self._store.setdefault("__users__", {})
            user.id = user.id or str(len(users) + 1) + "-u"
            users[user.id] = user.model_dump(exclude_none=True)
            return users[user.id]

    async def get_user(self, _id: str) -> Optional[dict]:
        return self._store.get("__users__", {}).get(_id)

    async def get_user_by_email(self, email: str) -> Optional[dict]:
        users = self._store.get("__users__", {})
        for user in users.values():
            if user.get("email") == email:
                return user
        return None

    async def list_users(self) -> List[Dict]:
        return list(self._store.get("__users__", {}).values())

    async def delete_user(self, _id: str) -> bool:
        async with self._lock:
            if _id in self._store.get("__users__", {}):
                del self._store["__users__"][_id]
                return True
            return False

    # UserRole operations
    async def save_user_role(self, user_role: UserRole) -> dict:
        async with self._lock:
            user_roles = self._store.setdefault("__user_roles__", {})
            user_role.id = user_role.id or str(len(user_roles) + 1) + "-ur"
            user_roles[user_role.id] = user_role.model_dump(exclude_none=True)
            return user_roles[user_role.id]

    async def get_user_roles(self, user_id: str) -> List[Dict]:
        roles = self._store.get("__user_roles__", {})
        return [role for role in roles.values() if role.get("user_id") == user_id]

    async def get_user_roles_by_company(self, user_id: str, company_id: str) -> List[Dict]:
        roles = self._store.get("__user_roles__", {})
        return [role for role in roles.values()
                if role.get("user_id") == user_id and role.get("company_id") == company_id]

    async def delete_user_role(self, _id: str) -> bool:
        async with self._lock:
            if _id in self._store.get("__user_roles__", {}):
                del self._store["__user_roles__"][_id]
                return True
            return False

    # Permission checking
    async def check_user_permission(self, user_id: str, company_id: str, screen: str, permission: str) -> bool:
        """Check if user has specific permission for a screen in a company"""
        user_roles = await self.get_user_roles_by_company(user_id, company_id)
        if not user_roles:
            return False

        for user_role in user_roles:
            role_id = user_role.get("role_id")
            if not role_id:
                continue
                
            role = await self.get_role(role_id)
            if not role:
                continue

            # Check role permissions
            role_id_from_role = role.get("id")
            if not role_id_from_role:
                continue
                
            permissions = await self.get_role_permissions(role_id_from_role)
            for perm in permissions:
                if (perm.get("screen") == screen and
                    permission in perm.get("permissions", [])):
                    return True

        return False

    # Get user profile with expanded information
    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        user = await self.get_user(user_id)
        if not user:
            return None

        user_roles = await self.get_user_roles(user_id)
        companies = []

        for role in user_roles:
            company_id = role.get("company_id")
            if company_id:
                company = await self.get_company(company_id)
                if company:
                    companies.append(company)

        # Expand roles with role details
        expanded_roles = []
        for user_role in user_roles:
            role_id = user_role.get("role_id")
            if role_id:
                role = await self.get_role(role_id)
                if role:
                    expanded_role = {
                        **user_role,
                        "role_details": role
                    }
                    expanded_roles.append(expanded_role)

        profile_data = {
            **user,
            "roles": expanded_roles,
            "companies": companies
        }

        return UserProfile(**profile_data)

    # UserInvitation operations
    async def save_user_invitation(self, invitation: UserInvitation) -> dict:
        async with self._lock:
            invitation.id = invitation.id or str(len(self._store) + 1) + "-inv"
            self._store.setdefault("__user_invitations__", {})[invitation.id] = invitation.model_dump(exclude_none=True)
            return self._store["__user_invitations__"][invitation.id]

    async def get_user_invitation_by_token(self, token: str) -> Optional[dict]:
        invitations = self._store.get("__user_invitations__", {})
        for invitation in invitations.values():
            if invitation.get("invitation_token") == token:
                return invitation
        return None

    async def get_user_invitations_by_email(self, email: str) -> List[Dict]:
        invitations = self._store.get("__user_invitations__", {})
        return [inv for inv in invitations.values() if inv.get("email") == email]

    async def update_user_invitation_status(self, invitation_id: str, status: str) -> bool:
        async with self._lock:
            if invitation_id in self._store.get("__user_invitations__", {}):
                self._store["__user_invitations__"][invitation_id]["status"] = status
                return True
            return False

    # PasswordResetToken operations
    async def save_password_reset_token(self, reset_token: PasswordResetToken) -> dict:
        async with self._lock:
            reset_token.id = reset_token.id or str(len(self._store) + 1) + "-rst"
            self._store.setdefault("__password_reset_tokens__", {})[reset_token.id] = reset_token.model_dump(exclude_none=True)
            return self._store["__password_reset_tokens__"][reset_token.id]

    async def get_password_reset_token(self, token: str) -> Optional[dict]:
        tokens = self._store.get("__password_reset_tokens__", {})
        for reset_token in tokens.values():
            if reset_token.get("reset_token") == token and not reset_token.get("used", False):
                return reset_token
        return None

    async def mark_password_reset_token_used(self, token_id: str) -> bool:
        async with self._lock:
            if token_id in self._store.get("__password_reset_tokens__", {}):
                self._store["__password_reset_tokens__"][token_id]["used"] = True
                return True
            return False

    async def delete_role_permission(self, _id: str) -> bool:
        async with self._lock:
            if _id in self._store.get("__role_permissions__", {}):
                del self._store["__role_permissions__"][_id]
                return True
            return False

    # Company Application operations
    async def save_company_application(self, application: CompanyApplication) -> dict:
        async with self._lock:
            if not application.id:
                app_count = len(self._store.get("__company_applications__", {}))
                application.id = str(app_count + 1) + "-ca"
            
            app_data = application.model_dump(exclude_none=True)
            self._store.setdefault("__company_applications__", {})[application.id] = app_data
            return self._store["__company_applications__"][application.id]

    async def get_company_application(self, application_id: str) -> Optional[dict]:
        return self._store.get("__company_applications__", {}).get(application_id)

    async def list_company_applications(self, 
                                       status: Optional[str] = None, 
                                       company_type: Optional[str] = None) -> List[dict]:
        applications = list(self._store.get("__company_applications__", {}).values())
        
        if status:
            applications = [app for app in applications if app.get("status") == status]
        if company_type:
            applications = [app for app in applications if app.get("company_type") == company_type]
            
        return applications

    async def update_company_application_status(self, 
                                               application_id: str, 
                                               status: str, 
                                               reviewer_id: str, 
                                               notes: str) -> bool:
        async with self._lock:
            applications = self._store.get("__company_applications__", {})
            if application_id in applications:
                applications[application_id]["status"] = status
                applications[application_id]["reviewer_id"] = reviewer_id
                applications[application_id]["reviewer_notes"] = notes
                applications[application_id]["reviewed_at"] = datetime.utcnow().isoformat()
                applications[application_id]["updated_at"] = datetime.utcnow().isoformat()
                return True
            return False

    async def update_company_application(self, application_id: str, updates: dict) -> bool:
        async with self._lock:
            applications = self._store.get("__company_applications__", {})
            if application_id in applications:
                applications[application_id].update(updates)
                applications[application_id]["updated_at"] = datetime.utcnow().isoformat()
                return True
            return False

    async def get_company_applications_by_status(self, status: str) -> List[dict]:
        applications = self._store.get("__company_applications__", {}).values()
        return [app for app in applications if app.get("status") == status]


class MongoRepo:
    def __init__(self, uri: str):
        if motor is None:
            raise RuntimeError("Motor not available")
        self._client = motor.AsyncIOMotorClient(uri)
        # Extract database name from URI or use default
        from urllib.parse import urlparse
        parsed_uri = urlparse(uri)
        db_name = parsed_uri.path.lstrip('/') if parsed_uri.path else 'openkiosk'
        self._db = self._client[db_name]
        self._col = self._db["content_metadata"]

    async def save(self, meta: ContentMetadata) -> dict:
        data = meta.model_dump(exclude_none=True)
        if not data.get("id"):
            import uuid
            data["id"] = str(uuid.uuid4())
        await self._col.replace_one({"id": data["id"]}, data, upsert=True)
        return data

    async def get(self, _id: str) -> Optional[dict]:
        return await self._col.find_one({"id": _id})

    async def list(self) -> List[Dict]:
        cursor = self._col.find({})
        return [d async for d in cursor]

    # ContentMeta operations
    @property
    def _content_meta_col(self):
        return self._db["content_meta"]

    async def save_content_meta(self, meta: ContentMeta) -> dict:
        data = meta.model_dump(exclude_none=True)
        if not data.get("id"):
            import uuid
            data["id"] = str(uuid.uuid4())
        await self._content_meta_col.replace_one({"id": data["id"]}, data, upsert=True)
        return data

    async def get_content_meta(self, _id: str) -> Optional[dict]:
        return await self._content_meta_col.find_one({"id": _id})

    async def list_content_meta(self) -> List[Dict]:
        cursor = self._content_meta_col.find({})
        return [d async for d in cursor]

    # Role operations
    @property
    def _role_col(self):
        return self._db["roles"]

    async def save_role(self, role: Role) -> dict:
        data = role.model_dump(exclude_none=True)
        if not data.get("id"):
            import uuid
            data["id"] = str(uuid.uuid4())
        await self._role_col.replace_one({"id": data["id"]}, data, upsert=True)
        return data

    async def get_role(self, _id: str) -> Optional[dict]:
        return await self._role_col.find_one({"id": _id})

    async def list_roles_by_company(self, company_id: str) -> List[Dict]:
        cursor = self._role_col.find({"company_id": company_id})
        return [d async for d in cursor]

    async def list_roles_by_group(self, role_group: str) -> List[Dict]:
        cursor = self._role_col.find({"role_group": role_group})
        return [d async for d in cursor]

    async def get_default_roles_by_company(self, company_id: str) -> List[Dict]:
        cursor = self._role_col.find({"company_id": company_id, "is_default": True})
        return [d async for d in cursor]

    async def delete_role(self, _id: str) -> bool:
        result = await self._role_col.delete_one({"id": _id})
        return result.deleted_count > 0

    # RolePermission operations
    @property
    def _role_permission_col(self):
        return self._db["role_permissions"]

    async def save_role_permission(self, permission: RolePermission) -> dict:
        data = permission.model_dump(exclude_none=True)
        if not data.get("id"):
            import uuid
            data["id"] = str(uuid.uuid4())
        await self._role_permission_col.replace_one({"id": data["id"]}, data, upsert=True)
        return data

    async def get_role_permissions(self, role_id: str) -> List[Dict]:
        cursor = self._role_permission_col.find({"role_id": role_id})
        return [d async for d in cursor]

    # moderation related
    @property
    def _rev_col(self):
        return self._db["reviews"]

    async def save_review(self, review: dict) -> dict:
        if not review.get("id"):
            import uuid
            review["id"] = str(uuid.uuid4())
        await self._rev_col.replace_one({"id": review["id"]}, review, upsert=True)
        return review

    async def list_reviews(self) -> List[Dict]:
        cursor = self._rev_col.find({})
        return [d async for d in cursor]

    # Company operations
    @property
    def _company_col(self):
        return self._db["companies"]

    async def save_company(self, company: Company) -> dict:
        data = company.model_dump(exclude_none=True)
        if not data.get("id"):
            import uuid
            data["id"] = str(uuid.uuid4())
        await self._company_col.replace_one({"id": data["id"]}, data, upsert=True)
        return data

    async def get_company(self, _id: str) -> Optional[dict]:
        return await self._company_col.find_one({"id": _id})

    async def list_companies(self) -> List[Dict]:
        cursor = self._company_col.find({})
        return [d async for d in cursor]

    async def delete_company(self, _id: str) -> bool:
        result = await self._company_col.delete_one({"id": _id})
        return result.deleted_count > 0

    # User operations
    @property
    def _user_col(self):
        return self._db["users"]

    async def save_user(self, user: User) -> dict:
        data = user.model_dump(exclude_none=True)
        if not data.get("id"):
            import uuid
            data["id"] = str(uuid.uuid4())
        await self._user_col.replace_one({"id": data["id"]}, data, upsert=True)
        return data

    async def get_user(self, _id: str) -> Optional[dict]:
        return await self._user_col.find_one({"id": _id})

    async def get_user_by_email(self, email: str) -> Optional[dict]:
        return await self._user_col.find_one({"email": email})

    async def list_users(self) -> List[Dict]:
        cursor = self._user_col.find({})
        return [d async for d in cursor]

    async def delete_user(self, _id: str) -> bool:
        result = await self._user_col.delete_one({"id": _id})
        return result.deleted_count > 0

    # UserRole operations
    @property
    def _user_role_col(self):
        return self._db["user_roles"]

    async def save_user_role(self, user_role: UserRole) -> dict:
        data = user_role.model_dump(exclude_none=True)
        if not data.get("id"):
            import uuid
            data["id"] = str(uuid.uuid4())
        await self._user_role_col.replace_one({"id": data["id"]}, data, upsert=True)
        return data

    async def get_user_roles(self, user_id: str) -> List[Dict]:
        cursor = self._user_role_col.find({"user_id": user_id})
        user_roles = []
        async for user_role_data in cursor:
            role_id = user_role_data.get("role_id")
            company_id = user_role_data.get("company_id")
            
            # Get role details
            role = None
            if role_id:
                role = await self.get_role(role_id)
            
            # Get company details
            company = None
            if company_id and company_id != "global":
                company = await self.get_company(company_id)
            
            # Convert ObjectIds to strings in role and company data
            if role and _OBJECTID_AVAILABLE and ObjectId is not None:
                role = {k: str(v) if isinstance(v, ObjectId) else v for k, v in role.items()}
            if company and _OBJECTID_AVAILABLE and ObjectId is not None:
                company = {k: str(v) if isinstance(v, ObjectId) else v for k, v in company.items()}
            
            # Expand user role with details
            expanded_role = {
                **user_role_data,
                "id": str(user_role_data["_id"]),
                "role": role.get("role_group", "") if role else "",
                "role_name": role.get("name", "") if role else "",
                "company_name": company.get("name", "Unknown") if company else ("System" if company_id == "global" else "Unknown"),
                "role_details": role
            }
            user_roles.append(expanded_role)
        
        return user_roles

    async def get_user_roles_by_company(self, user_id: str, company_id: str) -> List[Dict]:
        cursor = self._user_role_col.find({"user_id": user_id, "company_id": company_id})
        return [d async for d in cursor]

    async def delete_user_role(self, _id: str) -> bool:
        result = await self._user_role_col.delete_one({"id": _id})
        return result.deleted_count > 0

    # Permission checking
    async def check_user_permission(self, user_id: str, company_id: str, screen: str, permission: str) -> bool:
        """Check if user has specific permission for a screen in a company"""
        user_roles = await self.get_user_roles_by_company(user_id, company_id)
        if not user_roles:
            return False

        for user_role in user_roles:
            role_id = user_role.get("role_id")
            if not role_id:
                continue
                
            role = await self.get_role(role_id)
            if not role:
                continue

            # Check role permissions
            role_id_from_role = role.get("id")
            if not role_id_from_role:
                continue
                
            permissions = await self.get_role_permissions(role_id_from_role)
            for perm in permissions:
                if (perm.get("screen") == screen and
                    permission in perm.get("permissions", [])):
                    return True

        return False

    # Get user profile with expanded information
    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        user = await self.get_user(user_id)
        if not user:
            return None

        # Convert ObjectIds in user data
        if _OBJECTID_AVAILABLE and ObjectId is not None:
            user = {k: str(v) if isinstance(v, ObjectId) else v for k, v in user.items()}

        user_roles = await self.get_user_roles(user_id)
        companies = []

        for role in user_roles:
            company_id = role.get("company_id")
            if company_id and company_id != "global":
                company = await self.get_company(company_id)
                if company:
                    # Convert ObjectIds in company data
                    if _OBJECTID_AVAILABLE and ObjectId is not None:
                        company = {k: str(v) if isinstance(v, ObjectId) else v for k, v in company.items()}
                    companies.append(company)

        profile_data = {
            **user,
            "roles": user_roles,
            "companies": companies
        }

        return UserProfile(**profile_data)

    # UserInvitation operations
    @property
    def _user_invitation_col(self):
        return self._db["user_invitations"]

    async def save_user_invitation(self, invitation: UserInvitation) -> dict:
        data = invitation.model_dump(exclude_none=True)
        if not data.get("id"):
            import uuid
            data["id"] = str(uuid.uuid4())
        await self._user_invitation_col.replace_one({"id": data["id"]}, data, upsert=True)
        return data

    async def get_user_invitation_by_token(self, token: str) -> Optional[dict]:
        return await self._user_invitation_col.find_one({"invitation_token": token})

    async def get_user_invitations_by_email(self, email: str) -> List[Dict]:
        cursor = self._user_invitation_col.find({"email": email})
        return [d async for d in cursor]

    async def update_user_invitation_status(self, invitation_id: str, status: str) -> bool:
        result = await self._user_invitation_col.update_one(
            {"id": invitation_id},
            {"$set": {"status": status}}
        )
        return result.modified_count > 0

    # PasswordResetToken operations
    @property
    def _password_reset_col(self):
        return self._db["password_reset_tokens"]

    async def save_password_reset_token(self, reset_token: PasswordResetToken) -> dict:
        data = reset_token.model_dump(exclude_none=True)
        if not data.get("id"):
            import uuid
            data["id"] = str(uuid.uuid4())
        await self._password_reset_col.replace_one({"id": data["id"]}, data, upsert=True)
        return data

    async def get_password_reset_token(self, token: str) -> Optional[dict]:
        return await self._password_reset_col.find_one({"reset_token": token, "used": False})

    async def mark_password_reset_token_used(self, token_id: str) -> bool:
        result = await self._password_reset_col.update_one(
            {"id": token_id},
            {"$set": {"used": True}}
        )
        return result.modified_count > 0

    # Company Application operations
    @property
    def _company_application_col(self):
        return self._db["company_applications"]

    async def save_company_application(self, application: CompanyApplication) -> dict:
        data = application.model_dump(exclude_none=True)
        if not data.get("id"):
            import uuid
            data["id"] = str(uuid.uuid4())
        await self._company_application_col.replace_one({"id": data["id"]}, data, upsert=True)
        return data

    async def get_company_application(self, application_id: str) -> Optional[dict]:
        return await self._company_application_col.find_one({"id": application_id})

    async def list_company_applications(self, 
                                       status: Optional[str] = None, 
                                       company_type: Optional[str] = None) -> List[dict]:
        query = {}
        if status:
            query["status"] = status
        if company_type:
            query["company_type"] = company_type
        
        cursor = self._company_application_col.find(query).sort("submitted_at", -1)
        return [doc async for doc in cursor]

    async def update_company_application_status(self, 
                                               application_id: str, 
                                               status: str, 
                                               reviewer_id: str, 
                                               notes: str) -> bool:
        result = await self._company_application_col.update_one(
            {"id": application_id},
            {"$set": {
                "status": status,
                "reviewer_id": reviewer_id,
                "reviewer_notes": notes,
                "reviewed_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }}
        )
        return result.modified_count > 0

    async def update_company_application(self, application_id: str, updates: dict) -> bool:
        updates["updated_at"] = datetime.utcnow()
        result = await self._company_application_col.update_one(
            {"id": application_id},
            {"$set": updates}
        )
        return result.modified_count > 0

    async def get_company_applications_by_status(self, status: str) -> List[dict]:
        cursor = self._company_application_col.find({"status": status}).sort("submitted_at", -1)
        return [doc async for doc in cursor]


# choose repo implementation
if _MONGO_AVAILABLE:
    repo = MongoRepo(settings.MONGO_URI)
else:
    repo = InMemoryRepo()
