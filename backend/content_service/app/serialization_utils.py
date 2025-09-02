"""Utilities for handling MongoDB ObjectId serialization"""

def clean_mongo_object(obj):
    """
    Recursively clean MongoDB objects for JSON serialization
    Converts ObjectId to string and handles nested objects
    """
    if obj is None:
        return None
    
    if isinstance(obj, dict):
        cleaned = {}
        for key, value in obj.items():
            # Convert _id to id and handle ObjectId conversion
            if key == "_id":
                cleaned["id"] = str(value)
            else:
                cleaned[key] = clean_mongo_object(value)
        return cleaned
    
    elif isinstance(obj, list):
        return [clean_mongo_object(item) for item in obj]
    
    elif hasattr(obj, '__dict__') or str(type(obj)) == "<class 'bson.objectid.ObjectId'>":
        return str(obj)
    
    else:
        return obj


def clean_user_data(user_data):
    """Clean user data specifically for API responses"""
    if not user_data:
        return None
    
    cleaned = clean_mongo_object(user_data)
    
    # Remove sensitive data
    cleaned.pop("hashed_password", None)
    
    return cleaned


def transform_user_for_frontend(user_data):
    """
    Transform backend user data to match frontend User interface expectations
    """
    if not user_data:
        return None
    
    # Clean MongoDB objects first
    user = clean_user_data(user_data)
    
    # Ensure user is a dict
    if not isinstance(user, dict):
        return None
    
    # Parse name into first_name and last_name
    name = user.get("name", "")
    name_parts = name.split(" ", 1)
    first_name = name_parts[0] if name_parts else ""
    last_name = name_parts[1] if len(name_parts) > 1 else ""
    
    # Determine user_type based on roles and email
    user_type = "COMPANY_USER"  # Default
    company_role = None
    permissions = []
    company_id = None
    
    roles = user.get("roles", [])
    if roles:
        # Check for SUPER_USER (admin with global company)
        for role in roles:
            if role.get("company_id") == "global" and role.get("role") == "ADMIN":
                user_type = "SUPER_USER"
                break
            elif role.get("company_id") != "global":
                # Company user
                company_id = role.get("company_id")
                company_role = role.get("role")
                break
    
    # For super users, give all permissions
    if user_type == "SUPER_USER":
        permissions = [
            "user_view", "user_create", "user_edit", "user_delete",
            "device_view", "device_create", "device_edit", "device_delete",
            "content_view", "content_create", "content_edit", "content_delete", 
            "content_approve", "content_share",
            "analytics_view", "platform_admin"
        ]
    
    # Transform to frontend format
    frontend_user = {
        "id": user.get("id"),
        "email": user.get("email"),
        "first_name": first_name,
        "last_name": last_name,
        "phone": user.get("phone"),
        "user_type": user_type,
        "company_id": company_id,
        "company_role": company_role,
        "permissions": permissions,
        "is_active": user.get("status") == "active",
        "last_login": user.get("last_login"),
        "roles": roles,  # Keep original roles for compatibility
        "created_at": user.get("created_at"),
        "updated_at": user.get("updated_at"),
        "email_verified": user.get("email_verified", False)
    }
    
    return frontend_user
