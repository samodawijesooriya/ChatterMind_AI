import os
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from pymongo import MongoClient
from .models import Document
from django.core.files.storage import FileSystemStorage
import bcrypt
from bson import ObjectId
from .models import Chatbot
import uuid


client = MongoClient("mongodb+srv://798white:SgOe9IxCwPEZIx1L@chatterbot.zv9ev.mongodb.net/?retryWrites=true&w=majority&appName=chatterbot")
db = client.get_database('chatterbot')
users_collection = db.get_collection('users')
chatbots_collection = db.get_collection('chatbots')
documents_collection = db.get_collection('documents')
def settings(request):
    if request.method == "POST":
        return update_profile(request)  # Handle profile update if form submitted

    # Get user details from session
    username = request.session.get('username')
    if not username:
        return redirect('login')

    user = users_collection.find_one({'username': username})
    return render(request, 'settings.html', {'user': user})

def update_profile(request):
    if request.method == "POST":
        username = request.session.get('username')
        if not username:
            return redirect('login')

        new_email = request.POST.get('email')
        new_username = request.POST.get('username')
        new_password = request.POST.get('password')

        update_data = {'email': new_email, 'username': new_username}
        if new_password:
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            update_data['password'] = hashed_password

        users_collection.update_one({'username': username}, {'$set': update_data})
        request.session['username'] = new_username  # Update session with new username

        return HttpResponse("Profile updated successfully!")

    return redirect('settings')

def toggle_theme(request):
    if request.method == "POST":
        dark_mode = request.session.get('dark_mode', False)
        request.session['dark_mode'] = not dark_mode  # Toggle dark mode
        return JsonResponse({'dark_mode': request.session['dark_mode']})

    return redirect('settings')

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
            return HttpResponse("Login successful!")
        else:
            return HttpResponse("Invalid credentials!")
    return render(request, 'login.html')

# 🔹 Home Page
def home(request):
    if "username" not in request.session:
        return redirect("login")

    username = request.session["username"]
    
    chatbots = chatbots_collection.find({"username": username})
    print("chatbot Data: ", chatbots)

    return render(request, "home.html", {
        "username": username,
        "chatbots": chatbots,
    })

def create_chatbot(request):
    if request.method == "POST":

        if "username" not in request.session:
            return redirect("login")

        user = request.session["username"]
        chatbot_name = request.POST.get("name")
        uploaded_file = request.FILES.get("document")

        if not chatbot_name or not uploaded_file:
            return render(request, "chatbot_form.html", {"error": "All fields are required!"})


        chatbot_id = str(uuid.uuid4())

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
            "chatbot_id": chatbot_id,
            "username": user,
            "chatbot_name": chatbot_name,
            "file_path": file_path.replace(settings.MEDIA_ROOT, "media"),  # Store relative path
        }
        chatbots_collection.insert_one(chatbot_data)

        return redirect("home")  # Replace with your success URL

    return render(request, "new_chatbot.html")


def view_uploads(request, chatbot_name):
    user = request.session.get("username")
    if not user:
        return redirect("login")

    # Fetch chatbot details from MongoDB
    chatbot_data = chatbots_collection.find_one({"username": user, "chatbot_name": chatbot_name})

    if not chatbot_data:
        return render(request, "error.html", {"message": "Chatbot not found!"})

    # Get the chatbot's folder path
    chatbot_folder = os.path.join(settings.MEDIA_ROOT, "uploads", user, chatbot_name)

    # List all files in the chatbot's folder
    if os.path.exists(chatbot_folder):
        files = os.listdir(chatbot_folder)
    else:
        files = []

    return render(request, "view_uploads.html", {"chatbot_name": chatbot_name, "files": files, "user": user})

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

def chatbot_detail(request, chatbot_name):
    chatbot = chatbots_collection.find_one({"chatbot_name": chatbot_name})

    if not chatbot:
        return render(request, "chatbot_detail.html", {"error": "Chatbot not found!"})

    return render(request, "chatbot_detail.html", {"chatbot": chatbot})