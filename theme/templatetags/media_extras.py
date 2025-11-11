from django import template
from django.conf import settings
from django.core.files.storage import default_storage
from django.templatetags.static import static

register = template.Library()


def _file_exists(field) -> bool:
    try:
        if not field:
            return False
        name = getattr(field, 'name', '') or ''
        if not name:
            return False
        return default_storage.exists(name)
    except Exception:
        return False


@register.simple_tag
def resolve_avatar_url(doctor=None, user=None, default_static='images/default-avatar.svg'):
    """Return a safe URL for avatar from doctor.avatar or user.extras.avatar; fallback to static default if file missing."""
    # Try doctor.avatar first
    try_order = []
    if doctor is not None:
        try_order.append(getattr(doctor, 'avatar', None))
        # Some models nest user extras under doctor.user.extras
        try:
            try_order.append(getattr(getattr(getattr(doctor, 'user', None), 'extras', None), 'avatar', None))
        except Exception:
            pass
    if user is not None:
        try_order.append(getattr(getattr(user, 'extras', None), 'avatar', None))

    for field in try_order:
        if _file_exists(field):
            try:
                return field.url
            except Exception:
                continue

    # Fallback to static default
    return static(default_static)


