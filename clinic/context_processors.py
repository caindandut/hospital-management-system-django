"""
Context processors for DUT Hospital System
"""
from core.choices import Role


def role_flags(request):
    """
    Context processor to add role flags to all templates
    
    Returns:
        dict: Dictionary containing role flags
    """
    if not request.user.is_authenticated:
        return {
            "IS_AUTH": False,
            "IS_PATIENT": False,
            "IS_DOCTOR": False,
            "IS_STAFF": False,
            "IS_ADMIN": False,
            "USER_ROLE": None,
            "USER_ROLE_DISPLAY": None,
        }
    
    # Find role from ExternalUser table by email
    user_role = None
    try:
        from accounts.models import Users as ExternalUser
        email = getattr(request.user, 'email', None)
        if email:
            ext_user = ExternalUser.objects.filter(email=email).first()
            if ext_user:
                user_role = ext_user.role
    except Exception:
        pass
    
    return {
        "IS_AUTH": True,
        "IS_PATIENT": user_role == Role.PATIENT,
        "IS_DOCTOR": user_role == Role.DOCTOR,
        "IS_STAFF": user_role == Role.STAFF,
        "IS_ADMIN": user_role == Role.ADMIN,
        "USER_ROLE": user_role,
        "USER_ROLE_DISPLAY": dict(Role.choices).get(user_role, "Không xác định") if user_role else "Không xác định",
    }


def user_info(request):
    """
    Context processor to add user information to all templates
    
    Returns:
        dict: Dictionary containing user information
    """
    if not request.user.is_authenticated:
        return {
            "CURRENT_USER": None,
            "USER_FULL_NAME": None,
            "USER_EMAIL": None,
        }
    
    # Get user info from ExternalUser table (accounts.models.Users)
    user_full_name = getattr(request.user, 'full_name', '')
    user_email = getattr(request.user, 'email', '')
    
    try:
        from accounts.models import Users as ExternalUser
        email = getattr(request.user, 'email', None)
        if email:
            ext_user = ExternalUser.objects.filter(email=email).first()
            if ext_user:
                # Use full_name from ExternalUser if available
                if hasattr(ext_user, 'full_name') and ext_user.full_name:
                    user_full_name = ext_user.full_name
                if hasattr(ext_user, 'email') and ext_user.email:
                    user_email = ext_user.email
    except Exception:
        pass
    
    return {
        "CURRENT_USER": request.user,
        "USER_FULL_NAME": user_full_name,
        "USER_EMAIL": user_email,
    }
