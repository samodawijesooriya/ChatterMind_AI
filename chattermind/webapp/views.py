import os
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings
from pymongo import MongoClient
from .models import Document
from django.core.files.storage import FileSystemStorage
import bcrypt
from bson import ObjectId

client = MongoClient("mongodb+srv://798white:SgOe9IxCwPEZIx1L@chatterbot.zv9ev.mongodb.net/?retryWrites=true&w=majority&appName=chatterbot")
db = client.get_database('chatterbot')
users_collection = db.get_collection('users')
chatbots_collection = db.get_collection('chatbots')

def register(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        # Save user to MongoDB
        if users_collection.find_one({'username': username}):
            return HttpResponse("Username already exists!")
        users_collection.insert_one({'username': username, 'password': hashed_password})
        return HttpResponse("Registration successful!")
    return render(request, 'register.html')

def login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        # Check user in MongoDB
        user = users_collection.find_one({'username': username})
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            request.session['username'] = username
            return redirect('home')
        else:
            return HttpResponse("Invalid credentials!")
    return render(request, 'login.html')

# 🔹 Home Page
def home(request):
    if "username" not in request.session:
        return redirect("login")
    return render(request, 'home.html', {'username': request.session['username']})

def create_chatbot(request):
    if request.method == "POST":

        if "username" not in request.session:
            return redirect("login")

        user = request.session["username"]
        chatbot_name = request.POST.get("name")
        uploaded_file = request.FILES.get("document")

        if not chatbot_name or not uploaded_file:
            return render(request, "chatbot_form.html", {"error": "All fields are required!"})

        # Define the chatbot directory inside media/uploads/{username}/{chatbot_name}/
        chatbot_folder = os.path.join(settings.MEDIA_ROOT, "uploads", user, chatbot_name)
        os.makedirs(chatbot_folder, exist_ok=True)  # Create the directory if it doesn't exist

        # Save the uploaded file inside media/uploads/{username}/{chatbot_name}/
        file_path = os.path.join(chatbot_folder, uploaded_file.name)
        with open(file_path, "wb+") as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        # Store chatbot details in MongoDB
        chatbot_data = {
            "username": user,
            "chatbot_name": chatbot_name,
            "file_path": file_path.replace(settings.MEDIA_ROOT, "media"),  # Store relative path
        }
        chatbots_collection.insert_one(chatbot_data)

        return redirect("home")  # Replace with your success URL

    return render(request, "new_chatbot.html")

def view_uploads(request):
    if "username" not in request.session:
        return redirect("login")

    username = request.session["username"]
    user_files = list(documents_collection.find({'username': username}))

    return render(request, "view_uploads.html", {'files': user_files})

def delete_document(request, file_name):
    # Find the document by file_name
    document = documents_collection.find_one({"file_name": file_name})

    if document:
        # Delete the file from storage
        file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', file_name)
        if os.path.exists(file_path):
            os.remove(file_path)

        # Delete the document from MongoDB
        documents_collection.delete_one({"file_name": file_name})

    return redirect("view_uploads")


def chatbot_dashboard(request):
    
    # Render the template with the chatbots (empty or populated)
    return render(request, 'chatbot_dashboard.html')

def new_chatbot(request):
    if "username" not in request.session:
        return redirect("login")

    return render(request, 'new_chatbot.html')

