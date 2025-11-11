from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
import re
from django.utils.http import url_has_allowed_host_and_scheme
from django.conf import settings
from accounts.models import Users as ExternalUser
from patients.models import PatientProfiles as PatientProfile
from django.db import connection
from django.db.utils import OperationalError, ProgrammingError
from django.utils import timezone
from django.contrib.auth.hashers import check_password

def get_user_by_login_field(login_field):
    """Helper function to find user by email, phone, or username in Django auth.User"""
    # Check if it's an email
    if '@' in login_field and '.' in login_field:
        try:
            return User.objects.get(email=login_field)
        except User.DoesNotExist:
            return None
    
    # Check if it's a phone number (contains only digits, +, -, spaces, parentheses)
    elif re.match(r'^[\+]?[0-9\s\-\(\)]+$', login_field):
        # For now, treat phone as username
        try:
            return User.objects.get(username=login_field)
        except User.DoesNotExist:
            return None
    
    # Otherwise, treat as username
    else:
        try:
            return User.objects.get(username=login_field)
        except User.DoesNotExist:
            return None

def external_users_available() -> bool:
    """Return True if 'users' table exists in the connected DB."""
    try:
        tables = connection.introspection.table_names()
        return 'users' in tables
    except Exception as e:
        return False

def get_external_user(login_field):
    """Find user in accounts.Users by email or phone, guarded by table existence."""
    if not external_users_available():
        return None
    try:
        if '@' in login_field and '.' in login_field:
            return ExternalUser.objects.get(email=login_field)
        elif re.match(r'^[\+]?[0-9\s\-\(\)]+$', login_field):
            return ExternalUser.objects.get(phone=login_field)
        else:
            # Treat as email fallback
            return ExternalUser.objects.get(email=login_field)
    except (ExternalUser.DoesNotExist, OperationalError, ProgrammingError):
        return None

def _sanitize_username(raw: str) -> str:
    """Keep only letters, numbers, dots, underscores, and dashes in username base."""
    return re.sub(r"[^A-Za-z0-9._-]", "", raw)[:150] or "user"

def generate_unique_username(base: str) -> str:
    base = _sanitize_username(base)
    if not User.objects.filter(username=base).exists():
        return base
    suffix = 1
    while True:
        candidate = f"{base}{suffix}"
        if not User.objects.filter(username=candidate).exists():
            return candidate
        suffix += 1

def home(request):
    """Redirect root to the login form."""
    # If already logged in, route to role-based landing
    if request.user.is_authenticated:
        return _redirect_after_login(request.user)
    return redirect('theme:login')

def _redirect_after_login(django_user):
    """Choose landing page based on external role or fallback."""
    try:
        ext = None
        if external_users_available():
            email = getattr(django_user, 'email', None)
            if email:
                ext = ExternalUser.objects.filter(email=email).first()
        role = getattr(ext, 'role', None)
        if django_user.is_staff or django_user.is_superuser or role == 'ADMIN':
            return redirect('/admin-portal/')
        if role == 'DOCTOR':
            from django.urls import reverse
            return redirect('appointments:appt_doctor_today')
        if role == 'STAFF':
            return redirect('staff:staff_cashier')
        # Default: patient → go to my appointments
        return redirect('appointments:my_appointments')
    except Exception:
        # Safe fallback
        return redirect('appointments:my_appointments')

def login_view(request):
    """Login view"""
    next_url = request.GET.get('next') or request.POST.get('next') or ''
    if request.method == 'POST':
        login_field = request.POST.get('login_field')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        
        # 1) Try external users table first (only if available)
        ext_user = get_external_user(login_field)
        if ext_user:
            if not bool(ext_user.is_active):
                messages.error(request, 'Tài khoản đã bị vô hiệu hóa!')
                return render(request, 'auth/login.html', { 'next': next_url })
            
            stored = getattr(ext_user, 'password_hash', '') or ''
            # Support Django-compatible hash formats or plaintext
            matched = False
            try:
                matched = check_password(password, stored)
            except Exception:
                matched = False
            if not matched:
                matched = (password == stored)
            
            if matched:
                # Ensure a Django auth user exists and log them in
                username_base = ext_user.email.split('@')[0] if getattr(ext_user, 'email', None) else str(ext_user.id)
                existing = User.objects.filter(email=getattr(ext_user, 'email', None)).first()
                django_user = existing or User.objects.create_user(
                    username=generate_unique_username(username_base or 'user'),
                    email=getattr(ext_user, 'email', '') or generate_unique_username(username_base or 'user')
                )
                django_user.set_unusable_password()
                # Update profile names if possible
                try:
                    full_name = (getattr(ext_user, 'full_name', '') or '').strip()
                    parts = full_name.split()
                    django_user.first_name = parts[0] if parts else ''
                    django_user.last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''
                except Exception:
                    pass
                django_user.is_active = True
                django_user.save()
                # Login and session expiry
                django_user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, django_user)
                request.session.set_expiry(60 * 60 * 24 * 14 if remember else 0)
                if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                    return redirect(next_url)
                messages.success(request, 'Đăng nhập thành công!')
                # Check if user is admin and redirect accordingly
                return _redirect_after_login(django_user)
            else:
                messages.error(request, 'Mật khẩu không đúng!')
                return render(request, 'auth/login.html', { 'next': next_url })
        
        # 2) Fallback to Django auth.User
        user_obj = get_user_by_login_field(login_field)
        if user_obj:
            user = authenticate(request, username=user_obj.username, password=password)
            if user is not None:
                login(request, user)
                request.session.set_expiry(60 * 60 * 24 * 14 if remember else 0)
                if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                    return redirect(next_url)
                messages.success(request, 'Đăng nhập thành công!')
                # Check if user is admin and redirect accordingly
                return _redirect_after_login(user)
            else:
                messages.error(request, 'Mật khẩu không đúng!')
                return render(request, 'auth/login.html', { 'next': next_url })
        else:
            messages.error(request, 'Email/số điện thoại không tồn tại!')
            return render(request, 'auth/login.html', { 'next': next_url })
    
    return render(request, 'auth/login.html', { 'next': next_url })

def validate_password(password):
    """Validate password strength"""
    errors = []
    
    if len(password) < 8:
        errors.append('Mật khẩu phải có ít nhất 8 ký tự')
    
    if not re.search(r'[A-Z]', password):
        errors.append('Mật khẩu phải có ít nhất 1 chữ hoa')
    
    if not re.search(r'[a-z]', password):
        errors.append('Mật khẩu phải có ít nhất 1 chữ thường')
    
    if not re.search(r'[0-9]', password):
        errors.append('Mật khẩu phải có ít nhất 1 chữ số')
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append('Mật khẩu phải có ít nhất 1 ký tự đặc biệt (!@#$%^&*(),.?":{}|<>)')
    
    return errors

def register_view(request):
    """Register view"""
    if request.method == 'POST':
        # username will be auto-generated
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        terms = request.POST.get('terms')
        
        # Validation
        if not terms:
            messages.error(request, 'Vui lòng đồng ý với điều khoản sử dụng!')
        elif password1 != password2:
            messages.error(request, 'Mật khẩu xác nhận không khớp!')
        elif not email:
            messages.error(request, 'Vui lòng nhập email!')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email đã được sử dụng!')
        else:
            # Validate password strength
            password_errors = validate_password(password1)
            if password_errors:
                for error in password_errors:
                    messages.error(request, error)
            else:
                try:
                    # Prefer using phone as username if provided, otherwise use email local-part
                    if phone:
                        base_username = re.sub(r"\D", "", phone)  # keep digits only
                    else:
                        base_username = (email.split('@')[0] if '@' in email else email)
                    username = generate_unique_username(base_username)
                    
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password1,
                        first_name=first_name,
                        last_name=last_name
                    )
                    
                    # Mirror into external users table if available (simple plaintext password_hash as per your data)
                    if external_users_available():
                        full_name = f"{first_name} {last_name}".strip()
                        try:
                            ExternalUser.objects.create(
                                email=email,
                                password_hash=password1,
                                full_name=full_name,
                                phone=phone or None,
                                role='PATIENT',
                                is_active=1,
                                created_at=timezone.now(),
                                updated_at=timezone.now(),
                            )
                        except Exception:
                            # Ignore if schema differs or row already exists
                            pass
                    
                    messages.success(request, 'Đăng ký thành công! Vui lòng đăng nhập.')
                    return redirect('theme:login')
                except Exception as e:
                    messages.error(request, 'Có lỗi xảy ra khi tạo tài khoản. Vui lòng thử lại!')
    
    return render(request, 'auth/register.html')

def logout_view(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'Đăng xuất thành công!')
    return redirect('theme:login')

def profile_view(request):
    """Profile page (requires login). Routes to appropriate profile based on user role."""
    if not request.user.is_authenticated:
        return redirect('theme:login')

    # Check if user is staff/admin
    if request.user.is_staff or request.user.is_superuser:
        messages.info(request, 'Quản trị viên vui lòng quản lý thông tin qua Admin Portal')
        return redirect('/admin-portal/')
    
    # Map Django auth user -> external Users by email (fallback by username)
    ext_user = None
    if external_users_available():
        email = getattr(request.user, 'email', None)
        if email:
            ext_user = ExternalUser.objects.filter(email=email).first()
        if not ext_user:
            full_name = f"{request.user.first_name} {request.user.last_name}".strip()
            ext_user = ExternalUser.objects.filter(full_name=full_name).first()

    # Check user role and redirect to appropriate profile
    if ext_user:
        if ext_user.role == 'DOCTOR':
            return redirect('doctors:profile')
        elif ext_user.role == 'STAFF':
            return redirect('staff:profile_self')
    
    # If no ext_user found, try to create one as PATIENT
    if not ext_user and external_users_available():
        try:
            from django.utils import timezone
            ext_user = ExternalUser.objects.create(
                email=request.user.email or f"{request.user.username}@example.com",
                password_hash="",  # Empty for now
                full_name=f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
                phone="",
                role='PATIENT',
                is_active=1,
                created_at=timezone.now(),
                updated_at=timezone.now(),
            )
        except Exception:
            pass

    profile = None
    if ext_user:
        profile = PatientProfile.objects.filter(user_id=ext_user.id).first()

    if request.method == 'POST':
        try:
            # Ensure we have ext_user before proceeding
            if not ext_user and external_users_available():
                try:
                    from django.utils import timezone
                    
                    # Prepare data for external user
                    email = request.user.email or f"{request.user.username}@example.com"
                    full_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
                    
                    # Check if email already exists
                    existing_user = ExternalUser.objects.filter(email=email).first()
                    if existing_user:
                        print(f"External user with email {email} already exists: {existing_user.id}")
                        ext_user = existing_user
                    else:
                        ext_user = ExternalUser.objects.create(
                            email=email,
                            password_hash="temp_password",  # Non-empty value
                            full_name=full_name,
                            phone="",
                            role='PATIENT',
                            is_active=1,
                            created_at=timezone.now(),
                            updated_at=timezone.now(),
                        )
                    
                    # Update profile variable since we now have ext_user
                    profile = PatientProfile.objects.filter(user_id=ext_user.id).first()
                except Exception as e:
                    import traceback
                    raise e
            

            # Update user's full name and email if provided
            full_name = request.POST.get('full_name')
            if full_name:
                name_parts = full_name.strip().split()
                request.user.first_name = name_parts[0] if name_parts else ''
                request.user.last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
                request.user.save(update_fields=['first_name', 'last_name'])
            
            email = request.POST.get('email')
            if email and email != request.user.email:
                request.user.email = email
                request.user.save(update_fields=['email'])
            
            # Update phone in external user if available
            phone = request.POST.get('phone')
            if phone and ext_user:
                ext_user.phone = phone
                ext_user.save(update_fields=['phone'])
            
            # Save to patient_profiles - now we should have ext_user
            if ext_user:
                
                # Save submitted fields to patient_profiles (create or update)
                data = {
                    'cccd': request.POST.get('cccd') or (profile.cccd if profile else None),
                    'date_of_birth': request.POST.get('date_of_birth') or None,
                    'gender': request.POST.get('gender') or None,
                    'address': request.POST.get('address') or None,
                    'insurance_number': request.POST.get('insurance_number') or None,
                    'emergency_contact_name': request.POST.get('emergency_contact_name') or None,
                    'emergency_contact_phone': request.POST.get('emergency_contact_phone') or None,
                    'blood_type': request.POST.get('blood_type') or None,
                    'allergies': request.POST.get('allergies') or None,
                    'notes': request.POST.get('notes') or None,
                }
                
                
                if profile:
                    for k, v in data.items():
                        if v is not None and v != '':  # Only update non-empty values
                            setattr(profile, k, v)
                    profile.save()
                else:
                    try:
                        # Check if CCCD is required and provided
                        if not data.get('cccd'):
                            from django.utils import timezone
                            data['cccd'] = f"TEMP_{ext_user.id}_{timezone.now().strftime('%Y%m%d%H%M%S')}"
                        
                        # Remove None and empty values
                        clean_data = {k: v for k, v in data.items() if v is not None and v != ''}
                        
                        profile = PatientProfile.objects.create(user=ext_user, **clean_data)
                    except Exception as create_error:
                        # Try to create with minimal data
                        try:
                            from django.utils import timezone
                            minimal_data = {
                                'cccd': f"TEMP_{ext_user.id}_{timezone.now().strftime('%Y%m%d%H%M%S')}",
                            }
                            profile = PatientProfile.objects.create(user=ext_user, **minimal_data)
                            
                            # Now update with the actual data
                            for k, v in data.items():
                                if k != 'cccd' and v is not None and v != '':  # Don't overwrite the generated CCCD
                                    setattr(profile, k, v)
                            profile.save()
                        except Exception as minimal_error:
                            raise create_error
            else:
                if external_users_available():
                    error_msg = "Không thể lưu thông tin hồ sơ. Vui lòng thử lại."
                else:
                    error_msg = "Hệ thống đang sử dụng SQLite. Vui lòng cấu hình MySQL để lưu thông tin hồ sơ."
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': error_msg
                    })
                else:
                    messages.error(request, error_msg)
                    return redirect('theme:profile')
            
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Cập nhật hồ sơ thành công!'
                })
            else:
                messages.success(request, 'Cập nhật hồ sơ thành công!')
                return redirect('theme:profile')
                
        except Exception as e:
            import traceback
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': f'Có lỗi xảy ra khi lưu thông tin: {str(e)}'
                })
            else:
                messages.error(request, f'Có lỗi xảy ra khi lưu thông tin: {str(e)}')
                return redirect('theme:profile')

    context = {
        'ext_user': ext_user,
        'profile': profile,
    }
    return render(request, 'profile/patient_profile.html', context)

def change_password_view(request):
    """Change password view"""
    if not request.user.is_authenticated:
        return redirect('theme:login')
    
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validation
        if not current_password:
            messages.error(request, 'Vui lòng nhập mật khẩu hiện tại!')
        elif not new_password:
            messages.error(request, 'Vui lòng nhập mật khẩu mới!')
        elif not confirm_password:
            messages.error(request, 'Vui lòng xác nhận mật khẩu mới!')
        elif new_password != confirm_password:
            messages.error(request, 'Mật khẩu xác nhận không khớp!')
        elif len(new_password) < 8:
            messages.error(request, 'Mật khẩu mới phải có ít nhất 8 ký tự!')
        else:
            # Check current password against external users table
            password_valid = False
            ext_user = None
            
            if external_users_available():
                ext_user = ExternalUser.objects.filter(email=request.user.email).first()
                if ext_user:
                    stored = getattr(ext_user, 'password_hash', '') or ''
                    print(f"DEBUG: User email: {request.user.email}")
                    print(f"DEBUG: Stored password hash: {stored}")
                    print(f"DEBUG: Current password: {current_password}")
                    
                    # Support Django-compatible hash formats or plaintext
                    try:
                        password_valid = check_password(current_password, stored)
                        print(f"DEBUG: Django check_password result: {password_valid}")
                    except Exception as e:
                        print(f"DEBUG: Django check_password error: {e}")
                        password_valid = False
                    if not password_valid:
                        password_valid = (current_password == stored)
                        print(f"DEBUG: Plain text comparison result: {password_valid}")
                else:
                    print(f"DEBUG: No external user found for email: {request.user.email}")
            else:
                print("DEBUG: External users table not available")
            
            if password_valid and ext_user:
                try:
                    # Update password in external users table
                    ext_user.password_hash = new_password
                    ext_user.save(update_fields=['password_hash'])
                    
                    # Also update Django auth user (optional, for consistency)
                    request.user.set_password(new_password)
                    request.user.save()
                    
                    messages.success(request, 'Đổi mật khẩu thành công! Vui lòng đăng nhập lại.')
                    return redirect('theme:login')
                except Exception as e:
                    messages.error(request, f'Có lỗi xảy ra khi đổi mật khẩu: {str(e)}')
            else:
                messages.error(request, 'Mật khẩu hiện tại không đúng!')
    
    return render(request, 'auth/change_password.html')

