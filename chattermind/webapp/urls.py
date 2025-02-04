from django.urls import path
from . import views
from .views import upload_document 
from .views import delete_document



urlpatterns = [
    path('login/', views.login, name='login'),
    path('home/login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('home/', views.home, name='home'),
    path("home/upload.html", views.upload_document, name="upload"),
    path('view_uploads/', views.view_uploads, name='view_uploads'),
    path('home/view-documents/', views.view_uploads, name='view_doc'),
    path("delete/<str:file_name>/", delete_document, name="delete_document"),


    path('home/dashboard/', views.chatbot_dashboard, name='chatbot_dashboard'),
    path('home/history/', views.chatbot_history, name='chatbot_history'),
    path('home/new_chatbot/', views.new_chatbot, name='new_chatbot'),
    path('home/chatbot/<int:chatbot_id>/', views.view_chatbot, name='view_chatbot'),
]

