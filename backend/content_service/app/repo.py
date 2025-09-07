from typing import Optional, Dict, List
import asyncio
import logging
from datetime import datetime, timedelta
from app.models import (
    ContentMetadata, ContentMeta, Company, User, UserRole, Role, RolePermission, UserProfile, 
    UserInvitation, PasswordResetToken, CompanyApplication, CompanyApplicationStatus, 
    DigitalScreen, DigitalTwin, DeviceRegistrationKey, ContentCategory, ContentTag, HostPreference,
    DeviceCredentials, DeviceHeartbeat, DeviceFingerprint, DeviceCapabilities
)
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
        # Only return items that look like ContentMetadata (have title field)
        all_items = list(self._store.values())
        content_metadata_items = [
            item for item in all_items
            if isinstance(item, dict) and "title" in item
        ]
        return content_metadata_items

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
            
            # Check for existing company with same name or organization code
            for existing_id, existing_company in companies.items():
                if existing_company.get("name") == company.name:
                    logger.warning(f"Company with name '{company.name}' already exists (ID: {existing_id})")
                    return existing_company  # Return existing instead of creating duplicate
                
                if existing_company.get("organization_code") == company.organization_code:
                    logger.warning(f"Company with organization code '{company.organization_code}' already exists (ID: {existing_id})")
                    return existing_company  # Return existing instead of creating duplicate
            
            # Generate ID for new company
            company.id = company.id or str(len(companies) + 1) + "-c"
            company_data = company.model_dump(exclude_none=True)
            companies[company.id] = company_data
            logger.info(f"Created new company: {company.name} (ID: {company.id})")
            return company_data

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

    # DigitalScreen operations
    async def save_digital_screen(self, screen: DigitalScreen) -> dict:
        async with self._lock:
            screens = self._store.setdefault("__digital_screens__", {})
            screen.id = screen.id or str(len(screens) + 1) + "-ds"
            screens[screen.id] = screen.model_dump(exclude_none=True)
            return screens[screen.id]

    async def get_digital_screen(self, _id: str) -> Optional[dict]:
        return self._store.get("__digital_screens__", {}).get(_id)

    async def save_digital_twin(self, twin: DigitalTwin) -> dict:
        async with self._lock:
            twins = self._store.setdefault("__digital_twins__", {})
            twin.id = twin.id or str(len(twins) + 1) + "-dt"
            twins[twin.id] = twin.model_dump(exclude_none=True)
            return twins[twin.id]

    async def get_digital_twin(self, _id: str) -> Optional[dict]:
        return self._store.get("__digital_twins__", {}).get(_id)

    async def list_digital_twins(self, company_id: Optional[str] = None) -> List[dict]:
        async with self._lock:
            twins = self._store.get("__digital_twins__", {}).values()
            if company_id:
                return [twin for twin in twins if twin.get("company_id") == company_id]
            return list(twins)

    async def get_digital_twin_by_screen(self, screen_id: str) -> Optional[dict]:
        async with self._lock:
            twins = self._store.get("__digital_twins__", {}).values()
            for twin in twins:
                if twin.get("screen_id") == screen_id:
                    return twin
            return None

    # Device operations (for new RBAC system)
    async def save_device(self, device_data: dict) -> dict:
        async with self._lock:
            devices = self._store.setdefault("__devices__", {})
            device_data["id"] = device_data.get("id") or str(len(devices) + 1) + "-dev"
            devices[device_data["id"]] = device_data
            return devices[device_data["id"]]

    async def list_digital_screens(self, company_id: Optional[str] = None) -> List[Dict]:
        screens = list(self._store.get("__digital_screens__", {}).values())
        if company_id:
            screens = [s for s in screens if s.get("company_id") == company_id]
        return screens

    async def update_digital_screen(self, _id: str, updates: dict) -> bool:
        async with self._lock:
            screens = self._store.get("__digital_screens__", {})
            if _id in screens:
                screens[_id].update(updates)
                screens[_id]["updated_at"] = datetime.utcnow()  # Use datetime object instead of ISO string
                return True
            return False

    async def delete_digital_screen(self, _id: str) -> bool:
        async with self._lock:
            screens = self._store.get("__digital_screens__", {})
            if _id in screens:
                del screens[_id]
                return True
            return False

    # ContentOverlay operations
    async def save_content_overlay(self, overlay_dict: dict) -> dict:
        async with self._lock:
            overlays = self._store.setdefault("__content_overlays__", {})
            overlay_dict["id"] = overlay_dict.get("id") or str(len(overlays) + 1) + "-overlay"
            overlays[overlay_dict["id"]] = overlay_dict
            return overlays[overlay_dict["id"]]

    async def get_content_overlay(self, overlay_id: str) -> Optional[dict]:
        return self._store.get("__content_overlays__", {}).get(overlay_id)

    async def list_content_overlays(self, screen_id: Optional[str] = None, company_id: Optional[str] = None) -> List[Dict]:
        overlays = list(self._store.get("__content_overlays__", {}).values())
        if screen_id:
            overlays = [o for o in overlays if o.get("screen_id") == screen_id]
        if company_id:
            overlays = [o for o in overlays if o.get("company_id") == company_id]
        return overlays

    async def update_content_overlay(self, overlay_id: str, updates: dict) -> bool:
        async with self._lock:
            overlays = self._store.get("__content_overlays__", {})
            if overlay_id in overlays:
                overlays[overlay_id].update(updates)
                overlays[overlay_id]["updated_at"] = datetime.utcnow()
                return True
            return False

    async def delete_content_overlay(self, overlay_id: str) -> bool:
        async with self._lock:
            overlays = self._store.get("__content_overlays__", {})
            if overlay_id in overlays:
                del overlays[overlay_id]
                return True
            return False

    # DeviceRegistrationKey operations
    async def save_device_registration_key(self, key: DeviceRegistrationKey) -> dict:
        async with self._lock:
            keys = self._store.setdefault("__device_registration_keys__", {})
            key.id = key.id or str(len(keys) + 1) + "-key"
            keys[key.id] = key.model_dump(exclude_none=True)
            return keys[key.id]

    async def get_device_registration_key(self, key: str) -> Optional[dict]:
        keys = self._store.get("__device_registration_keys__", {})
        for k in keys.values():
            if k.get("key") == key:
                return k
        return None
    
    async def get_device_registration_key_by_id(self, key_id: str) -> Optional[dict]:
        keys = self._store.get("__device_registration_keys__", {})
        return keys.get(key_id)

    async def list_device_registration_keys(self, company_id: Optional[str] = None) -> List[Dict]:
        keys = list(self._store.get("__device_registration_keys__", {}).values())
        if company_id:
            keys = [k for k in keys if k.get("company_id") == company_id]
        return keys

    async def mark_key_used(self, key_id: str, device_id: str) -> bool:
        async with self._lock:
            keys = self._store.get("__device_registration_keys__", {})
            if key_id in keys:
                keys[key_id]["used"] = True
                keys[key_id]["used_at"] = datetime.utcnow().isoformat()
                keys[key_id]["used_by_device"] = device_id
                return True
            return False

    async def delete_device_registration_key(self, key_id: str) -> bool:
        async with self._lock:
            keys = self._store.get("__device_registration_keys__", {})
            if key_id in keys:
                del keys[key_id]
                return True
            return False

    # ContentCategory operations
    async def save_content_category(self, category: ContentCategory) -> dict:
        async with self._lock:
            categories = self._store.setdefault("__content_categories__", {})
            category.id = category.id or str(len(categories) + 1) + "-cat"
            categories[category.id] = category.model_dump(exclude_none=True)
            return categories[category.id]

    async def get_content_category(self, _id: str) -> Optional[dict]:
        return self._store.get("__content_categories__", {}).get(_id)

    async def list_content_categories(self, active_only: bool = True) -> List[Dict]:
        categories = list(self._store.get("__content_categories__", {}).values())
        if active_only:
            categories = [c for c in categories if c.get("is_active", True)]
        return categories

    async def update_content_category(self, _id: str, updates: dict) -> bool:
        async with self._lock:
            categories = self._store.get("__content_categories__", {})
            if _id in categories:
                categories[_id].update(updates)
                categories[_id]["updated_at"] = datetime.utcnow()
                return True
            return False

    async def delete_content_category(self, _id: str) -> bool:
        async with self._lock:
            categories = self._store.get("__content_categories__", {})
            if _id in categories:
                del categories[_id]
                return True
            return False

    # ContentTag operations
    async def save_content_tag(self, tag: ContentTag) -> dict:
        async with self._lock:
            tags = self._store.setdefault("__content_tags__", {})
            tag.id = tag.id or str(len(tags) + 1) + "-tag"
            tags[tag.id] = tag.model_dump(exclude_none=True)
            return tags[tag.id]

    async def get_content_tag(self, _id: str) -> Optional[dict]:
        return self._store.get("__content_tags__", {}).get(_id)

    async def list_content_tags(self, active_only: bool = True, category_id: Optional[str] = None) -> List[Dict]:
        tags = list(self._store.get("__content_tags__", {}).values())
        if active_only:
            tags = [t for t in tags if t.get("is_active", True)]
        if category_id:
            tags = [t for t in tags if t.get("category_id") == category_id]
        return tags

    async def update_content_tag(self, _id: str, updates: dict) -> bool:
        async with self._lock:
            tags = self._store.get("__content_tags__", {})
            if _id in tags:
                tags[_id].update(updates)
                tags[_id]["updated_at"] = datetime.utcnow()
                return True
            return False

    async def delete_content_tag(self, _id: str) -> bool:
        async with self._lock:
            tags = self._store.get("__content_tags__", {})
            if _id in tags:
                del tags[_id]
                return True
            return False

    # HostPreference operations
    async def save_host_preference(self, preference: HostPreference) -> dict:
        async with self._lock:
            preferences = self._store.setdefault("__host_preferences__", {})
            preference.id = preference.id or str(len(preferences) + 1) + "-pref"
            preferences[preference.id] = preference.model_dump(exclude_none=True)
            return preferences[preference.id]

    async def get_host_preferences(self, company_id: str, screen_id: Optional[str] = None) -> List[Dict]:
        preferences = list(self._store.get("__host_preferences__", {}).values())
        preferences = [p for p in preferences if p.get("company_id") == company_id]
        if screen_id:
            preferences = [p for p in preferences if p.get("screen_id") == screen_id or p.get("screen_id") is None]
        return preferences

    async def update_host_preference(self, _id: str, updates: dict) -> bool:
        async with self._lock:
            preferences = self._store.get("__host_preferences__", {})
            if _id in preferences:
                preferences[_id].update(updates)
                preferences[_id]["updated_at"] = datetime.utcnow()
                return True
            return False

    async def delete_host_preference(self, _id: str) -> bool:
        async with self._lock:
            preferences = self._store.get("__host_preferences__", {})
            if _id in preferences:
                del preferences[_id]
                return True
            return False

    # DeviceCredentials operations
    async def save_device_credentials(self, credentials: DeviceCredentials) -> dict:
        async with self._lock:
            creds = self._store.setdefault("__device_credentials__", {})
            credentials.id = credentials.id or str(len(creds) + 1) + "-cred"
            creds[credentials.id] = credentials.model_dump(exclude_none=True)
            return creds[credentials.id]

    async def get_device_credentials(self, device_id: str) -> Optional[dict]:
        creds = self._store.get("__device_credentials__", {})
        for cred in creds.values():
            if cred.get("device_id") == device_id and not cred.get("revoked", False):
                return cred
        return None

    async def revoke_device_credentials(self, device_id: str) -> bool:
        async with self._lock:
            creds = self._store.get("__device_credentials__", {})
            for cred_id, cred in creds.items():
                if cred.get("device_id") == device_id:
                    creds[cred_id]["revoked"] = True
                    creds[cred_id]["revoked_at"] = datetime.utcnow()
                    return True
            return False

    async def update_device_credentials(self, device_id: str, updates: dict) -> bool:
        async with self._lock:
            creds = self._store.get("__device_credentials__", {})
            for cred_id, cred in creds.items():
                if cred.get("device_id") == device_id and not cred.get("revoked", False):
                    creds[cred_id].update(updates)
                    creds[cred_id]["last_refreshed"] = datetime.utcnow()
                    return True
            return False

    # DeviceHeartbeat operations
    async def save_device_heartbeat(self, heartbeat: DeviceHeartbeat) -> dict:
        async with self._lock:
            heartbeats = self._store.setdefault("__device_heartbeats__", {})
            heartbeat.id = heartbeat.id or str(len(heartbeats) + 1) + "-hb"
            heartbeats[heartbeat.id] = heartbeat.model_dump(exclude_none=True)
            return heartbeats[heartbeat.id]

    async def get_latest_heartbeat(self, device_id: str) -> Optional[dict]:
        heartbeats = list(self._store.get("__device_heartbeats__", {}).values())
        device_heartbeats = [hb for hb in heartbeats if hb.get("device_id") == device_id]
        if device_heartbeats:
            # Return the most recent heartbeat
            return max(device_heartbeats, key=lambda x: x.get("timestamp", datetime.min))
        return None

    async def get_device_heartbeats(self, device_id: str, limit: int = 100) -> List[Dict]:
        heartbeats = list(self._store.get("__device_heartbeats__", {}).values())
        device_heartbeats = [hb for hb in heartbeats if hb.get("device_id") == device_id]
        # Sort by timestamp descending and limit results
        device_heartbeats.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)
        return device_heartbeats[:limit]

    async def cleanup_old_heartbeats(self, older_than_hours: int = 24) -> int:
        """Clean up heartbeats older than specified hours"""
        async with self._lock:
            heartbeats = self._store.get("__device_heartbeats__", {})
            cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
            
            old_heartbeat_ids = []
            for hb_id, heartbeat in heartbeats.items():
                timestamp = heartbeat.get("timestamp")
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp)
                if timestamp and timestamp < cutoff_time:
                    old_heartbeat_ids.append(hb_id)
            
            for hb_id in old_heartbeat_ids:
                del heartbeats[hb_id]
                
            return len(old_heartbeat_ids)

    # Enhanced device operations
    async def get_device_with_credentials(self, device_id: str) -> Optional[Dict]:
        """Get device with its credentials and latest heartbeat"""
        device = await self.get_digital_screen(device_id)
        if not device:
            return None
            
        credentials = await self.get_device_credentials(device_id)
        latest_heartbeat = await self.get_latest_heartbeat(device_id)
        
        return {
            "device": device,
            "credentials": credentials,
            "latest_heartbeat": latest_heartbeat
        }

    async def get_devices_by_status(self, status: Optional[str] = None, company_id: Optional[str] = None) -> List[Dict]:
        """Get devices filtered by status and/or company"""
        devices = await self.list_digital_screens(company_id)
        if status:
            devices = [d for d in devices if d.get("status") == status]
        return devices

    # Device Schedule operations
    async def create_device_schedule(self, schedule_data: dict) -> dict:
        """Create a device schedule"""
        async with self._lock:
            schedules = self._store.setdefault("__device_schedules__", {})
            if not schedule_data.get("id"):
                schedule_data["id"] = str(len(schedules) + 1) + "-schedule"
            
            schedule_data["created_at"] = datetime.utcnow()
            schedule_data["updated_at"] = datetime.utcnow()
            schedules[schedule_data["id"]] = schedule_data
            return schedules[schedule_data["id"]]

    async def get_device_schedule(self, device_id: str) -> Optional[dict]:
        """Get schedule for a specific device"""
        schedules = self._store.get("__device_schedules__", {})
        for schedule in schedules.values():
            if schedule.get("device_id") == device_id:
                return schedule
        return None

    async def update_device_schedule(self, schedule_id: str, updates: dict) -> bool:
        """Update a device schedule"""
        async with self._lock:
            schedules = self._store.get("__device_schedules__", {})
            if schedule_id in schedules:
                updates["updated_at"] = datetime.utcnow()
                schedules[schedule_id].update(updates)
                return True
            return False

    async def delete_device_schedule(self, schedule_id: str) -> bool:
        """Delete a device schedule"""
        async with self._lock:
            schedules = self._store.get("__device_schedules__", {})
            if schedule_id in schedules:
                del schedules[schedule_id]
                return True
            return False

    async def list_device_schedules(self, device_id: Optional[str] = None) -> List[dict]:
        """List device schedules, optionally filtered by device"""
        schedules = self._store.get("__device_schedules__", {})
        if device_id:
            return [s for s in schedules.values() if s.get("device_id") == device_id]
        return list(schedules.values())

    # Content Distribution operations
    async def save_content_distribution(self, distribution: dict) -> dict:
        async with self._lock:
            distributions = self._store.setdefault("__content_distributions__", {})
            distribution["id"] = distribution.get("id") or str(len(distributions) + 1) + "-dist"
            distributions[distribution["id"]] = distribution
            return distributions[distribution["id"]]

    async def get_content_distribution(self, distribution_id: str) -> Optional[dict]:
        return self._store.get("__content_distributions__", {}).get(distribution_id)

    async def list_content_distributions(self, content_id: Optional[str] = None, device_id: Optional[str] = None) -> List[Dict]:
        distributions = list(self._store.get("__content_distributions__", {}).values())
        if content_id:
            distributions = [d for d in distributions if d.get("content_id") == content_id]
        if device_id:
            distributions = [d for d in distributions if d.get("device_id") == device_id]
        return distributions

    async def update_content_distribution_status(self, distribution_id: str, status: str) -> bool:
        async with self._lock:
            distributions = self._store.get("__content_distributions__", {})
            if distribution_id in distributions:
                distributions[distribution_id]["status"] = status
                distributions[distribution_id]["updated_at"] = datetime.utcnow().isoformat()
                return True
            return False

    # Layout Template operations
    async def save_layout_template(self, template: dict) -> dict:
        async with self._lock:
            templates = self._store.setdefault("__layout_templates__", {})
            template["id"] = template.get("id") or str(len(templates) + 1) + "-lt"
            templates[template["id"]] = template
            return templates[template["id"]]

    async def get_layout_template(self, template_id: str) -> Optional[dict]:
        return self._store.get("__layout_templates__", {}).get(template_id)

    async def list_layout_templates(self, company_id: Optional[str] = None, is_public: Optional[bool] = None) -> List[Dict]:
        templates = list(self._store.get("__layout_templates__", {}).values())
        
        if company_id:
            templates = [
                t for t in templates 
                if t.get("company_id") == company_id or t.get("is_public")
            ]
        if is_public is not None:
            templates = [t for t in templates if t.get("is_public") == is_public]
        
        return templates

    async def update_layout_template(self, template_id: str, updates: dict) -> bool:
        async with self._lock:
            templates = self._store.get("__layout_templates__", {})
            if template_id in templates:
                templates[template_id].update(updates)
                templates[template_id]["updated_at"] = datetime.utcnow().isoformat()
                return True
            return False

    async def delete_layout_template(self, template_id: str) -> bool:
        async with self._lock:
            templates = self._store.get("__layout_templates__", {})
            if template_id in templates:
                del templates[template_id]
                return True
            return False

    async def increment_template_usage(self, template_id: str) -> bool:
        async with self._lock:
            templates = self._store.get("__layout_templates__", {})
            if template_id in templates:
                templates[template_id]["usage_count"] = templates[template_id].get("usage_count", 0) + 1
                return True
            return False

    # Content Overlay operations
    async def create_content_overlay(self, overlay_data: dict) -> dict:
        """Create a new content overlay definition"""
        async with self._lock:
            overlays = self._store.setdefault("__content_overlays__", {})
            if not overlay_data.get("id"):
                overlay_data["id"] = str(len(overlays) + 1) + "-overlay"
            
            overlay_data["created_at"] = datetime.utcnow()
            overlay_data["updated_at"] = datetime.utcnow()
            overlays[overlay_data["id"]] = overlay_data
            return overlays[overlay_data["id"]]

    async def get_content_overlay(self, overlay_id: str) -> Optional[dict]:
        """Get a specific content overlay by ID"""
        return self._store.get("__content_overlays__", {}).get(overlay_id)

    async def update_content_overlay(self, overlay_id: str, updates: dict) -> bool:
        """Update a content overlay"""
        async with self._lock:
            overlays = self._store.get("__content_overlays__", {})
            if overlay_id in overlays:
                updates["updated_at"] = datetime.utcnow()
                overlays[overlay_id].update(updates)
                return True
            return False

    async def delete_content_overlay(self, overlay_id: str) -> bool:
        """Delete a content overlay"""
        async with self._lock:
            overlays = self._store.get("__content_overlays__", {})
            if overlay_id in overlays:
                del overlays[overlay_id]
                return True
            return False

    async def get_content_overlays_by_screen(self, screen_id: str) -> List[dict]:
        """Get all content overlays for a specific screen"""
        overlays = self._store.get("__content_overlays__", {})
        return [overlay for overlay in overlays.values() if overlay.get("screen_id") == screen_id]

    async def get_content_overlays_by_host(self, host_id: str) -> List[dict]:
        """Get all content overlays created by a specific host"""
        overlays = self._store.get("__content_overlays__", {})
        return [overlay for overlay in overlays.values() if overlay.get("host_id") == host_id]

    async def get_user_role_in_company(self, user_id: str, company_id: str) -> Optional[Dict]:
        """Get user's primary role in a specific company"""
        user_roles = await self.get_user_roles_by_company(user_id, company_id)
        if not user_roles:
            return None
            
        # Find default role or first active role
        for user_role in user_roles:
            if user_role.get("is_default", False) and user_role.get("status") == "active":
                role_id = user_role.get("role_id")
                if role_id:
                    role = await self.get_role(role_id)
                    if role:
                        return {**user_role, "role_details": role}
        
        # If no default, return first active role
        for user_role in user_roles:
            if user_role.get("status") == "active":
                role_id = user_role.get("role_id")
                if role_id:
                    role = await self.get_role(role_id)
                    if role:
                        return {**user_role, "role_details": role}
        
        return None


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

    # ContentCategory operations
    @property
    def _content_category_col(self):
        return self._db["content_categories"]

    async def save_content_category(self, category: ContentCategory) -> dict:
        data = category.model_dump(exclude_none=True)
        if not data.get("id"):
            import uuid
            data["id"] = str(uuid.uuid4())
        await self._content_category_col.replace_one({"id": data["id"]}, data, upsert=True)
        return data

    async def get_content_category(self, _id: str) -> Optional[dict]:
        return await self._content_category_col.find_one({"id": _id})

    async def list_content_categories(self, active_only: bool = True) -> List[Dict]:
        query = {"is_active": True} if active_only else {}
        cursor = self._content_category_col.find(query)
        return [d async for d in cursor]

    async def update_content_category(self, _id: str, updates: dict) -> bool:
        updates["updated_at"] = datetime.utcnow()
        result = await self._content_category_col.update_one(
            {"id": _id},
            {"$set": updates}
        )
        return result.modified_count > 0

    async def delete_content_category(self, _id: str) -> bool:
        result = await self._content_category_col.delete_one({"id": _id})
        return result.deleted_count > 0

    # ContentTag operations
    @property
    def _content_tag_col(self):
        return self._db["content_tags"]

    async def save_content_tag(self, tag: ContentTag) -> dict:
        data = tag.model_dump(exclude_none=True)
        if not data.get("id"):
            import uuid
            data["id"] = str(uuid.uuid4())
        await self._content_tag_col.replace_one({"id": data["id"]}, data, upsert=True)
        return data

    async def get_content_tag(self, _id: str) -> Optional[dict]:
        return await self._content_tag_col.find_one({"id": _id})

    async def list_content_tags(self, active_only: bool = True) -> List[Dict]:
        query = {"is_active": True} if active_only else {}
        cursor = self._content_tag_col.find(query)
        return [d async for d in cursor]

    async def update_content_tag(self, _id: str, updates: dict) -> bool:
        updates["updated_at"] = datetime.utcnow()
        result = await self._content_tag_col.update_one(
            {"id": _id},
            {"$set": updates}
        )
        return result.modified_count > 0

    async def delete_content_tag(self, _id: str) -> bool:
        result = await self._content_tag_col.delete_one({"id": _id})
        return result.deleted_count > 0

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
        
        # Check for existing company with same name or organization code
        existing_by_name = await self._company_col.find_one({"name": data["name"]})
        existing_by_org_code = await self._company_col.find_one({"organization_code": data["organization_code"]})
        
        if existing_by_name:
            logger.warning(f"Company with name '{data['name']}' already exists (ID: {existing_by_name.get('id')})")
            return existing_by_name  # Return existing instead of creating duplicate
        
        if existing_by_org_code:
            logger.warning(f"Company with organization code '{data['organization_code']}' already exists (ID: {existing_by_org_code.get('id')})")
            return existing_by_org_code  # Return existing instead of creating duplicate
        
        # Generate ID for new company
        if not data.get("id"):
            import uuid
            data["id"] = str(uuid.uuid4())
        
        await self._company_col.replace_one({"id": data["id"]}, data, upsert=True)
        logger.info(f"Created new company: {data['name']} (ID: {data['id']})")
        return data

    async def get_company(self, _id: str) -> Optional[dict]:
        return await self._company_col.find_one({"_id": _id})

    async def list_companies(self) -> List[Dict]:
        cursor = self._company_col.find({})
        companies = []
        async for doc in cursor:
            # Convert ObjectIds to strings
            if _OBJECTID_AVAILABLE and ObjectId is not None:
                doc = {k: str(v) if isinstance(v, ObjectId) else v for k, v in doc.items()}
            companies.append(doc)
        return companies

    async def delete_company(self, _id: str) -> bool:
        result = await self._company_col.delete_one({"_id": _id})
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
                "company_name": company.get("name") if company else ("System" if company_id == "global" else None),
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
        return await self._company_application_col.find_one({"_id": application_id})

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

    # DigitalScreen operations
    @property
    def _digital_screen_col(self):
        return self._db["digital_screens"]

    async def save_digital_screen(self, screen: DigitalScreen) -> dict:
        data = screen.model_dump(exclude_none=True)
        if not data.get("id"):
            import uuid
            data["id"] = str(uuid.uuid4())
        await self._digital_screen_col.replace_one({"id": data["id"]}, data, upsert=True)
        return data

    async def get_digital_screen(self, _id: str) -> Optional[dict]:
        return await self._digital_screen_col.find_one({"id": _id})

    # DigitalTwin operations
    @property
    def _digital_twin_col(self):
        return self._db["digital_twins"]

    async def save_digital_twin(self, twin: DigitalTwin) -> dict:
        data = twin.model_dump(exclude_none=True)
        if not data.get("id"):
            import uuid
            data["id"] = str(uuid.uuid4())
        await self._digital_twin_col.replace_one({"id": data["id"]}, data, upsert=True)
        return data

    async def get_digital_twin(self, _id: str) -> Optional[dict]:
        return await self._digital_twin_col.find_one({"id": _id})

    async def list_digital_twins(self, company_id: Optional[str] = None) -> List[dict]:
        query = {"company_id": company_id} if company_id else {}
        cursor = self._digital_twin_col.find(query).sort("created_at", -1)
        return [doc async for doc in cursor]

    async def get_digital_twin_by_screen(self, screen_id: str) -> Optional[dict]:
        return await self._digital_twin_col.find_one({"screen_id": screen_id})

    # Device operations (for new RBAC system)
    @property
    def _device_col(self):
        return self._db["devices"]

    async def save_device(self, device_data: dict) -> dict:
        if not device_data.get("id"):
            import uuid
            device_data["id"] = str(uuid.uuid4())
        await self._device_col.replace_one({"id": device_data["id"]}, device_data, upsert=True)
        return device_data

    async def list_digital_screens(self, company_id: Optional[str] = None) -> List[Dict]:
        query = {}
        if company_id:
            query["company_id"] = company_id
        cursor = self._digital_screen_col.find(query)
        screens = []
        async for doc in cursor:
            # Convert ObjectIds to strings
            if _OBJECTID_AVAILABLE and ObjectId is not None:
                doc = {k: str(v) if isinstance(v, ObjectId) else v for k, v in doc.items()}
            screens.append(doc)
        return screens

    async def update_digital_screen(self, _id: str, updates: dict) -> bool:
        updates["updated_at"] = datetime.utcnow()
        result = await self._digital_screen_col.update_one(
            {"id": _id},
            {"$set": updates}
        )
        return result.modified_count > 0

    async def delete_digital_screen(self, _id: str) -> bool:
        result = await self._digital_screen_col.delete_one({"id": _id})
        return result.deleted_count > 0

    # ContentOverlay operations
    @property
    def _content_overlay_col(self):
        return self._db["content_overlays"]

    async def save_content_overlay(self, overlay_dict: dict) -> dict:
        if not overlay_dict.get("id"):
            import uuid
            overlay_dict["id"] = str(uuid.uuid4())
        await self._content_overlay_col.replace_one({"id": overlay_dict["id"]}, overlay_dict, upsert=True)
        return overlay_dict

    async def get_content_overlay(self, overlay_id: str) -> Optional[dict]:
        doc = await self._content_overlay_col.find_one({"id": overlay_id})
        if doc and _OBJECTID_AVAILABLE and ObjectId is not None:
            doc = {k: str(v) if isinstance(v, ObjectId) else v for k, v in doc.items()}
        return doc

    async def list_content_overlays(self, screen_id: Optional[str] = None, company_id: Optional[str] = None) -> List[Dict]:
        query = {}
        if screen_id:
            query["screen_id"] = screen_id
        if company_id:
            query["company_id"] = company_id
        cursor = self._content_overlay_col.find(query)
        overlays = []
        async for doc in cursor:
            # Convert ObjectIds to strings
            if _OBJECTID_AVAILABLE and ObjectId is not None:
                doc = {k: str(v) if isinstance(v, ObjectId) else v for k, v in doc.items()}
            overlays.append(doc)
        return overlays

    async def update_content_overlay(self, overlay_id: str, updates: dict) -> bool:
        updates["updated_at"] = datetime.utcnow()
        result = await self._content_overlay_col.update_one(
            {"id": overlay_id},
            {"$set": updates}
        )
        return result.modified_count > 0

    async def delete_content_overlay(self, overlay_id: str) -> bool:
        result = await self._content_overlay_col.delete_one({"id": overlay_id})
        return result.deleted_count > 0

    # DeviceRegistrationKey operations
    @property
    def _device_registration_key_col(self):
        return self._db["device_registration_keys"]

    async def save_device_registration_key(self, key: DeviceRegistrationKey) -> dict:
        data = key.model_dump(exclude_none=True)
        if not data.get("id"):
            import uuid
            data["id"] = str(uuid.uuid4())
        await self._device_registration_key_col.replace_one({"id": data["id"]}, data, upsert=True)
        return data

    async def get_device_registration_key(self, key: str) -> Optional[dict]:
        result = await self._device_registration_key_col.find_one({"key": key})
        if result and _OBJECTID_AVAILABLE and ObjectId is not None:
            # Convert ObjectIds to strings
            result = {k: str(v) if isinstance(v, ObjectId) else v for k, v in result.items()}
        return result
    
    async def get_device_registration_key_by_id(self, key_id: str) -> Optional[dict]:
        try:
            # Try to find by string ID first
            result = await self._device_registration_key_col.find_one({"id": key_id})
            if result:
                # Convert ObjectIds to strings
                if _OBJECTID_AVAILABLE and ObjectId is not None:
                    result = {k: str(v) if isinstance(v, ObjectId) else v for k, v in result.items()}
                return result
            
            # If not found and ObjectId is available, try ObjectId format
            if _OBJECTID_AVAILABLE and ObjectId is not None and hasattr(ObjectId, 'is_valid') and ObjectId.is_valid(key_id):
                result = await self._device_registration_key_col.find_one({"_id": ObjectId(key_id)})
                if result:
                    result["id"] = str(result["_id"])
                    # Convert ObjectIds to strings
                    if _OBJECTID_AVAILABLE and ObjectId is not None:
                        result = {k: str(v) if isinstance(v, ObjectId) else v for k, v in result.items()}
                    return result
                    
            return None
        except Exception as e:
            logger.error(f"Error getting device registration key by ID {key_id}: {e}")
            return None

    async def list_device_registration_keys(self, company_id: Optional[str] = None) -> List[Dict]:
        query = {}
        if company_id:
            query["company_id"] = company_id
        cursor = self._device_registration_key_col.find(query)
        keys = []
        async for doc in cursor:
            # Convert ObjectIds to strings
            if _OBJECTID_AVAILABLE and ObjectId is not None:
                doc = {k: str(v) if isinstance(v, ObjectId) else v for k, v in doc.items()}
            keys.append(doc)
        return keys

    async def mark_key_used(self, key_id: str, device_id: str) -> bool:
        result = await self._device_registration_key_col.update_one(
            {"id": key_id},
            {"$set": {
                "used": True,
                "used_at": datetime.utcnow(),
                "used_by_device": device_id
            }}
        )
        return result.modified_count > 0

    async def delete_device_registration_key(self, key_id: str) -> bool:
        result = await self._device_registration_key_col.delete_one({"id": key_id})
        return result.deleted_count > 0

    # Content Distribution operations
    @property
    def _content_distribution_col(self):
        return self._db["content_distributions"]

    async def save_content_distribution(self, distribution: dict) -> dict:
        if not distribution.get("id"):
            import uuid
            distribution["id"] = str(uuid.uuid4())
        await self._content_distribution_col.replace_one({"id": distribution["id"]}, distribution, upsert=True)
        return distribution

    async def get_content_distribution(self, distribution_id: str) -> Optional[dict]:
        return await self._content_distribution_col.find_one({"id": distribution_id})

    async def list_content_distributions(self, content_id: Optional[str] = None, device_id: Optional[str] = None) -> List[Dict]:
        query = {}
        if content_id:
            query["content_id"] = content_id
        if device_id:
            query["device_id"] = device_id
        cursor = self._content_distribution_col.find(query)
        return [d async for d in cursor]

    async def update_content_distribution_status(self, distribution_id: str, status: str) -> bool:
        result = await self._content_distribution_col.update_one(
            {"id": distribution_id},
            {"$set": {
                "status": status,
                "updated_at": datetime.utcnow()
            }}
        )
        return result.modified_count > 0

    # Layout Template operations
    @property
    def _layout_template_col(self):
        return self._db["layout_templates"]

    async def save_layout_template(self, template: dict) -> dict:
        if not template.get("id"):
            import uuid
            template["id"] = str(uuid.uuid4())
        await self._layout_template_col.replace_one({"id": template["id"]}, template, upsert=True)
        return template

    async def get_layout_template(self, template_id: str) -> Optional[dict]:
        return await self._layout_template_col.find_one({"id": template_id})

    async def list_layout_templates(self, company_id: Optional[str] = None, is_public: Optional[bool] = None) -> List[Dict]:
        query = {}
        if company_id:
            query["$or"] = [
                {"company_id": company_id},
                {"is_public": True}
            ]
        if is_public is not None:
            query["is_public"] = is_public
        
        cursor = self._layout_template_col.find(query)
        return [d async for d in cursor]

    async def update_layout_template(self, template_id: str, updates: dict) -> bool:
        updates["updated_at"] = datetime.utcnow()
        result = await self._layout_template_col.update_one(
            {"id": template_id},
            {"$set": updates}
        )
        return result.modified_count > 0

    async def delete_layout_template(self, template_id: str) -> bool:
        result = await self._layout_template_col.delete_one({"id": template_id})
        return result.deleted_count > 0

    async def increment_template_usage(self, template_id: str) -> bool:
        result = await self._layout_template_col.update_one(
            {"id": template_id},
            {"$inc": {"usage_count": 1}}
        )
        return result.modified_count > 0

    # DeviceCredentials operations
    @property
    def _device_credentials_col(self):
        return self._db["device_credentials"]

    async def save_device_credentials(self, credentials: DeviceCredentials) -> dict:
        data = credentials.model_dump(exclude_none=True)
        if not data.get("id"):
            import uuid
            data["id"] = str(uuid.uuid4())
        await self._device_credentials_col.replace_one({"id": data["id"]}, data, upsert=True)
        return data

    async def get_device_credentials(self, device_id: str) -> Optional[dict]:
        result = await self._device_credentials_col.find_one({"device_id": device_id, "revoked": False})
        if result and _OBJECTID_AVAILABLE and ObjectId is not None:
            # Convert ObjectIds to strings
            result = {k: str(v) if isinstance(v, ObjectId) else v for k, v in result.items()}
        return result

    async def revoke_device_credentials(self, device_id: str) -> bool:
        result = await self._device_credentials_col.update_one(
            {"device_id": device_id, "revoked": False},
            {"$set": {"revoked": True, "revoked_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    async def update_device_credentials(self, device_id: str, updates: dict) -> bool:
        updates["last_refreshed"] = datetime.utcnow()
        result = await self._device_credentials_col.update_one(
            {"device_id": device_id, "revoked": False},
            {"$set": updates}
        )
        return result.modified_count > 0

    # DeviceHeartbeat operations
    @property
    def _device_heartbeat_col(self):
        return self._db["device_heartbeats"]

    async def save_device_heartbeat(self, heartbeat: DeviceHeartbeat) -> dict:
        data = heartbeat.model_dump(exclude_none=True)
        if not data.get("id"):
            import uuid
            data["id"] = str(uuid.uuid4())
        await self._device_heartbeat_col.replace_one({"id": data["id"]}, data, upsert=True)
        return data

    async def get_latest_heartbeat(self, device_id: str) -> Optional[dict]:
        cursor = self._device_heartbeat_col.find({"device_id": device_id}).sort("timestamp", -1).limit(1)
        async for doc in cursor:
            # Convert ObjectIds to strings
            if _OBJECTID_AVAILABLE and ObjectId is not None:
                doc = {k: str(v) if isinstance(v, ObjectId) else v for k, v in doc.items()}
            return doc
        return None

    async def get_device_heartbeats(self, device_id: str, limit: int = 100) -> List[Dict]:
        cursor = self._device_heartbeat_col.find({"device_id": device_id}).sort("timestamp", -1).limit(limit)
        heartbeats = []
        async for doc in cursor:
            # Convert ObjectIds to strings
            if _OBJECTID_AVAILABLE and ObjectId is not None:
                doc = {k: str(v) if isinstance(v, ObjectId) else v for k, v in doc.items()}
            heartbeats.append(doc)
        return heartbeats

    async def cleanup_old_heartbeats(self, older_than_hours: int = 24) -> int:
        """Clean up heartbeats older than specified hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
        
        result = await self._device_heartbeat_col.delete_many({
            "timestamp": {"$lt": cutoff_time}
        })
        return result.deleted_count

    # Enhanced device operations
    async def get_device_with_credentials(self, device_id: str) -> Optional[Dict]:
        """Get device with its credentials and latest heartbeat"""
        device = await self.get_digital_screen(device_id)
        if not device:
            return None
            
        credentials = await self.get_device_credentials(device_id)
        latest_heartbeat = await self.get_latest_heartbeat(device_id)
        
        return {
            "device": device,
            "credentials": credentials,
            "latest_heartbeat": latest_heartbeat
        }

    async def get_devices_by_status(self, status: Optional[str] = None, company_id: Optional[str] = None) -> List[Dict]:
        """Get devices filtered by status and/or company"""
        devices = await self.list_digital_screens(company_id)
        if status:
            devices = [d for d in devices if d.get("status") == status]
        return devices

    # Device Schedule operations
    @property
    def _device_schedules_col(self):
        return self._db["device_schedules"]

    async def create_device_schedule(self, schedule_data: dict) -> dict:
        """Create a device schedule"""
        if not schedule_data.get("id"):
            import uuid
            schedule_data["id"] = str(uuid.uuid4())
        
        schedule_data["created_at"] = datetime.utcnow()
        schedule_data["updated_at"] = datetime.utcnow()
        
        await self._device_schedules_col.insert_one(schedule_data)
        
        # Convert ObjectIds to strings
        if _OBJECTID_AVAILABLE and ObjectId is not None:
            schedule_data = {k: str(v) if isinstance(v, ObjectId) else v for k, v in schedule_data.items()}
        
        return schedule_data

    async def get_device_schedule(self, device_id: str) -> Optional[dict]:
        """Get schedule for a specific device"""
        result = await self._device_schedules_col.find_one({"device_id": device_id})
        if result and _OBJECTID_AVAILABLE and ObjectId is not None:
            result = {k: str(v) if isinstance(v, ObjectId) else v for k, v in result.items()}
        return result

    async def update_device_schedule(self, schedule_id: str, updates: dict) -> bool:
        """Update a device schedule"""
        updates["updated_at"] = datetime.utcnow()
        result = await self._device_schedules_col.update_one(
            {"id": schedule_id},
            {"$set": updates}
        )
        return result.modified_count > 0

    async def delete_device_schedule(self, schedule_id: str) -> bool:
        """Delete a device schedule"""
        result = await self._device_schedules_col.delete_one({"id": schedule_id})
        return result.deleted_count > 0

    async def list_device_schedules(self, device_id: Optional[str] = None) -> List[dict]:
        """List device schedules, optionally filtered by device"""
        query = {"device_id": device_id} if device_id else {}
        cursor = self._device_schedules_col.find(query)
        schedules = []
        async for doc in cursor:
            if _OBJECTID_AVAILABLE and ObjectId is not None:
                doc = {k: str(v) if isinstance(v, ObjectId) else v for k, v in doc.items()}
            schedules.append(doc)
        return schedules

    # Content Overlay operations
    @property
    def _content_overlays_col(self):
        return self._db["content_overlays"]

    async def create_content_overlay(self, overlay_data: dict) -> dict:
        """Create a new content overlay definition"""
        if not overlay_data.get("id"):
            import uuid
            overlay_data["id"] = str(uuid.uuid4())
        
        overlay_data["created_at"] = datetime.utcnow()
        overlay_data["updated_at"] = datetime.utcnow()
        
        await self._content_overlays_col.insert_one(overlay_data)
        
        # Convert ObjectIds to strings
        if _OBJECTID_AVAILABLE and ObjectId is not None:
            overlay_data = {k: str(v) if isinstance(v, ObjectId) else v for k, v in overlay_data.items()}
        
        return overlay_data

    async def get_content_overlay(self, overlay_id: str) -> Optional[dict]:
        """Get a specific content overlay by ID"""
        result = await self._content_overlays_col.find_one({"id": overlay_id})
        if result and _OBJECTID_AVAILABLE and ObjectId is not None:
            result = {k: str(v) if isinstance(v, ObjectId) else v for k, v in result.items()}
        return result

    async def update_content_overlay(self, overlay_id: str, updates: dict) -> bool:
        """Update a content overlay"""
        updates["updated_at"] = datetime.utcnow()
        result = await self._content_overlays_col.update_one(
            {"id": overlay_id},
            {"$set": updates}
        )
        return result.modified_count > 0

    async def delete_content_overlay(self, overlay_id: str) -> bool:
        """Delete a content overlay"""
        result = await self._content_overlays_col.delete_one({"id": overlay_id})
        return result.deleted_count > 0

    async def get_content_overlays_by_screen(self, screen_id: str) -> List[dict]:
        """Get all content overlays for a specific screen"""
        cursor = self._content_overlays_col.find({"screen_id": screen_id})
        overlays = []
        async for doc in cursor:
            if _OBJECTID_AVAILABLE and ObjectId is not None:
                doc = {k: str(v) if isinstance(v, ObjectId) else v for k, v in doc.items()}
            overlays.append(doc)
        return overlays

    async def get_content_overlays_by_host(self, host_id: str) -> List[dict]:
        """Get all content overlays created by a specific host"""
        cursor = self._content_overlays_col.find({"host_id": host_id})
        overlays = []
        async for doc in cursor:
            if _OBJECTID_AVAILABLE and ObjectId is not None:
                doc = {k: str(v) if isinstance(v, ObjectId) else v for k, v in doc.items()}
            overlays.append(doc)
        return overlays

    async def get_active_overlays_for_content(self, content_id: str, screen_id: str) -> List[dict]:
        """Get active overlays for specific content on a screen"""
        cursor = self._content_overlays_col.find({
            "screen_id": screen_id,
            "is_active": True,
            "$or": [
                {"content_id": content_id},
                {"content_id": None}  # Global overlays
            ]
        })
        overlays = []
        async for doc in cursor:
            if _OBJECTID_AVAILABLE and ObjectId is not None:
                doc = {k: str(v) if isinstance(v, ObjectId) else v for k, v in doc.items()}
            overlays.append(doc)
        return overlays

    # Company-scoped access control methods
    async def check_user_company_access(self, user_id: str, target_company_id: str) -> bool:
        """Check if user has access to a specific company's data"""
        user_roles = await self.get_user_roles(user_id)
        
        # Check if user belongs to the target company
        for role in user_roles:
            if role.get("company_id") == target_company_id:
                return True
                
        # Check if user is a platform admin (global access)
        for role in user_roles:
            if role.get("company_id") == "global":
                role_id = role.get("role_id")
                if role_id:
                    role_data = await self.get_role(role_id)
                    if role_data and role_data.get("role_group") == "ADMIN":
                        return True
        
        return False

    async def get_user_accessible_companies(self, user_id: str) -> List[Dict]:
        """Get list of companies the user has access to"""
        user_roles = await self.get_user_roles(user_id)
        accessible_companies = []
        
        # Check for platform admin access (can see all companies)
        is_platform_admin = False
        for role in user_roles:
            if role.get("company_id") == "global":
                role_id = role.get("role_id")
                if role_id:
                    role_data = await self.get_role(role_id)
                    if role_data and role_data.get("role_group") == "ADMIN":
                        is_platform_admin = True
                        break
        
        if is_platform_admin:
            return await self.list_companies()
        
        # Get only companies user belongs to
        company_ids = set()
        for role in user_roles:
            company_id = role.get("company_id")
            if company_id and company_id != "global":
                company_ids.add(company_id)
        
        for company_id in company_ids:
            company = await self.get_company(company_id)
            if company:
                accessible_companies.append(company)
                
        return accessible_companies

    async def get_user_role_in_company(self, user_id: str, company_id: str) -> Optional[Dict]:
        """Get user's primary role in a specific company"""
        user_roles = await self.get_user_roles_by_company(user_id, company_id)
        if not user_roles:
            return None
            
        # Find default role or first active role
        for user_role in user_roles:
            if user_role.get("is_default", False) and user_role.get("status") == "active":
                role_id = user_role.get("role_id")
                if role_id:
                    role = await self.get_role(role_id)
                    if role:
                        return {**user_role, "role_details": role}
        
        # If no default, return first active role
        for user_role in user_roles:
            if user_role.get("status") == "active":
                role_id = user_role.get("role_id")
                if role_id:
                    role = await self.get_role(role_id)
                    if role:
                        return {**user_role, "role_details": role}
        
        return None

    async def check_content_access_permission(self, user_id: str, content_owner_id: str, action: str = "view") -> bool:
        """Check if user can access content based on company isolation"""
        # Get content owner's company
        owner = await self.get_user(content_owner_id)
        if not owner:
            return False
            
        # Get companies that own this content
        owner_roles = await self.get_user_roles(content_owner_id)
        content_company_ids = set()
        for role in owner_roles:
            company_id = role.get("company_id")
            if company_id and company_id != "global":
                content_company_ids.add(company_id)
        
        # Check if requesting user has access to any of these companies
        for company_id in content_company_ids:
            if await self.check_user_company_access(user_id, company_id):
                # Additional permission check based on action
                if action in ["edit", "delete"]:
                    # For edit/delete, check if user has appropriate permissions
                    has_permission = await self.check_user_permission(user_id, company_id, "content", action)
                    if has_permission:
                        return True
                else:
                    # For view, just company access is enough
                    return True
        
        return False


# Global repository instance
repo = None

def initialize_repository():
    """Initialize the repository with proper error handling and logging"""
    global repo
    
    mongo_uri = getattr(settings, "MONGO_URI", None)
    logger.info(f"MONGO_URI configured: {mongo_uri is not None}")
    
    if mongo_uri and _MONGO_AVAILABLE and motor is not None:
        try:
            logger.info(f"Attempting to connect to MongoDB: {mongo_uri}")
            repo = MongoRepo(mongo_uri)
            logger.info("✅ Successfully initialized MongoDB repository - DATA WILL PERSIST")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize MongoDB repository: {e}")
            logger.warning("⚠️  Falling back to in-memory storage - DATA WILL BE LOST ON RESTART")
            repo = InMemoryRepo()
            return False
    else:
        if not mongo_uri:
            logger.warning("⚠️  MONGO_URI not configured")
        if not _MONGO_AVAILABLE:
            logger.warning("⚠️  Motor (MongoDB driver) not available")
        logger.warning("⚠️  Using in-memory repository - DATA WILL BE LOST ON RESTART")
        repo = InMemoryRepo()
        return False

# Initialize repository on import
persistence_enabled = initialize_repository()
