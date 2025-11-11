from django.urls import path
from . import views

app_name = 'theme'

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    
    # Authentication
    path('auth/login/', views.login_view, name='login'),
    path('auth/register/', views.register_view, name='register'),
    path('auth/logout/', views.logout_view, name='logout'),

    # Profile
     path('profile/', views.profile_view, name='profile'),
     path('profile/change-password/', views.change_password_view, name='change_password'),
]
