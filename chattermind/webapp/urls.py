from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('settings/', views.settings, name='settings'),  # New settings page
    path('update-profile/', views.update_profile, name='update_profile'),  # For updating user info
    path('toggle-theme/', views.toggle_theme, name='toggle_theme'),  # For toggling dark mode
]
