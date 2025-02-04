from django.urls import path
from . import views
from .views import create_chatbot 
from .views import delete_document



urlpatterns = [
    path('login/', views.login, name='login'),
    path('home/login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('home/', views.home, name='home'),
    path('home/new_chatbot/', views.create_chatbot, name='new_chatbot'),
    path("home/new_chatbot/new_chatbot.html", views.create_chatbot, name="upload"),
    path('view_uploads/', views.view_uploads, name='view_uploads'),
    path('home/view-documents/', views.view_uploads, name='view_doc'),
    path("delete/<str:file_name>/", delete_document, name="delete_document"),
    path('home/dashboard/login/', views.login, name='login'),
]

