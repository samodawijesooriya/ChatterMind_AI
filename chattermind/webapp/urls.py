from django.urls import path
from . import views
from .views import create_chatbot 
from .views import delete_document



urlpatterns = [
    path('', views.landingpage, name='landingpage'),  # Landing page
    path('login/', views.login, name='login'),
    path('home/login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('home/', views.home, name='home'),
    path('home/new_chatbot/', views.create_chatbot, name='new_chatbot'),
    path("home/new_chatbot/new_chatbot.html", views.create_chatbot, name="upload"),
    path('view_uploads/', views.view_uploads, name='view_uploads'),
    path('home/view-documents/', views.view_uploads, name='view_doc'),
    path('view_uploads/<str:chatbot_name>/', views.view_uploads, name='view_uploads'),
    path("delete/<str:file_name>/", delete_document, name="delete_document"),
    path('home/dashboard/login/', views.login, name='login'),
    path('home/chatbot/<str:chatbot_name>/', views.chatbot_detail, name='chatbot_detail'),
    path('settings/', views.settings, name='settings'),  # New settings page
    path('update-profile/', views.update_profile, name='update_profile'),  # For updating user info
    path('toggle-theme/', views.toggle_theme, name='toggle_theme'),  # For toggling dark mode
    path('settings/', views.settings, name='settings'),  # New settings page
    path('update-profile/', views.update_profile, name='update_profile'),  # For updating user info
    path('toggle-theme/', views.toggle_theme, name='toggle_theme'),  # For toggling dark mode


    path('chatbot/', views.chatbot, name='chatbot'),
    path('get_response/', views.get_response, name='get_response'),  # For handling AJAX


    path('chatbot/', views.chatbot, name='chatbot'),
    path('get_response/', views.get_response, name='get_response'),  # For handling AJAX

]

