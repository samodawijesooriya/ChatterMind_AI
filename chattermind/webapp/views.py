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
from .models import ChatBot

client = MongoClient("mongodb+srv://798white:SgOe9IxCwPEZIx1L@chatterbot.zv9ev.mongodb.net/?retryWrites=true&w=majority&appName=chatterbot")
db = client.get_database('chatterbot')
users_collection = db.get_collection('users')
documents_collection = db.get_collection('documents')

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

def upload_document(request):
    if "username" not in request.session:
        return redirect("login")

    alert_message = None  # To store alert message

    if request.method == "POST" and request.FILES.get("document"):
        uploaded_file = request.FILES["document"]
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')

        # Ensure the upload directory exists
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        # Check if a file with the same name already exists in MongoDB
        existing_file = documents_collection.find_one({"file_name": uploaded_file.name})
        if existing_file:
            alert_message = "A file with the same name already exists!"
            return render(request, "upload.html", {"alert_message": alert_message})

        fs = FileSystemStorage(location=upload_dir)
        filename = fs.save(uploaded_file.name, uploaded_file)
        file_url = fs.url(os.path.join('uploads', filename))

        # Store file metadata in MongoDB
        result = documents_collection.insert_one({
            'username': request.session['username'],
            'file_name': filename,
            'file_url': file_url
        })

        return redirect("view_uploads")  # Redirect to view uploads page

    return render(request, "upload.html", {"alert_message": alert_message})

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
    # Try to fetch all available chatbots
    try:
        chatbots = ChatBot.objects.all()  # You might filter by the user or other criteria
        if not chatbots:
            no_chatbots_message = "Not created chatbots"
        else:
            no_chatbots_message = None
    except ChatBot.DoesNotExist:
        # If the table or data does not exist, set a message to inform the user
        chatbots = []
        no_chatbots_message = "Not created chatbots"
    
    return render(request, 'chatbot_dashboard.html', {'chatbots': chatbots, 'no_chatbots_message': no_chatbots_message})


def chatbot_history(request):
    # Show the history of a chatbot
    chatbots = ChatBot.objects.all()
    return render(request, 'chatbot_history.html', {'chatbots': chatbots})

def new_chatbot(request):
    if "username" not in request.session:
        return redirect("login")

    username = request.session["username"]


    # Create a new chatbot
    if request.method == 'POST':
        chatbot_name = request.POST['name']
        new_chatbot = ChatBot.objects.create(name=chatbot_name, user=user)
        return redirect('chatbot_dashboard')  # Redirect to the dashboard after creating a new bot
    return render(request, 'new_chatbot.html')

def view_chatbot(request, chatbot_id):
    chatbot = ChatBot.objects.get(id=chatbot_id)
    if request.method == 'POST':
        # Handle chatbot editing
        chatbot.name = request.POST['name']
        chatbot.save()
        return redirect('chatbot_dashboard')
    return render(request, 'view_chatbot.html', {'chatbot': chatbot})