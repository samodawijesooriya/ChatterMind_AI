import os
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from pymongo import MongoClient
from .models import Document, Chatbot
from django.core.files.storage import FileSystemStorage
import bcrypt
from bson import ObjectId
import uuid
import random
import string
import smtplib
from email.mime.text import MIMEText
from .chatbot import ChatBot # Import your chatbot class

client = MongoClient("mongodb+srv://798white:SgOe9IxCwPEZIx1L@chatterbot.zv9ev.mongodb.net/?retryWrites=true&w=majority&appName=chatterbot")
db = client.get_database('chatterbot')
users_collection = db.get_collection('users')
chatbots_collection = db.get_collection('chatbots')
documents_collection = db.get_collection('documents')
MEDIA_ROOT = 'media'


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
        return redirect('home')
    return render(request, 'register.html')

def login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        # Check user in MongoDB
        user = users_collection.find_one({'username': username})
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            return redirect('home')
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

def generate_unique_id():
    # Generate a random string of 10 characters (simple letters and numbers)
    while True:
        # Create random string with lowercase letters and digits
        chars = string.ascii_lowercase + string.digits
        random_id = ''.join(random.choice(chars) for _ in range(10))
        
        # Check if this ID already exists in the database
        if not chatbots_collection.find_one({"chatbot_id": random_id}):
            return random_id
        


def create_chatbot(request):
    if request.method == "POST":

        if "username" not in request.session:
            return redirect("login")

        user = request.session["username"]
        chatbot_name = request.POST.get("name")
        uploaded_file = request.FILES.get("document")

        if not chatbot_name or not uploaded_file:
            return render(request, "chatbot_form.html", {"error": "All fields are required!"})

        chatbot_id = chatbot_id = generate_unique_id()

        # Define the chatbot directory inside media/uploads/{username}/{chatbot_name}/
        chatbot_folder = os.path.join(MEDIA_ROOT, "uploads", user, chatbot_name)
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
            "file_path": file_path.replace(MEDIA_ROOT, "media"),  # Store relative path
        }
        chatbots_collection.insert_one(chatbot_data)

        return redirect("home")  # Replace with your success URL

    return render(request, "new_chatbot.html")

def upload_document(request, chatbot_name):
    if request.method == 'POST':
        if "username" not in request.session:
            return redirect("login")
        
        username = request.session["username"]
        chatbot_name = request.POST.get("ChatBotname")
        document = request.FILES['document']
        doc_name = document.name
        print("Document Name: ", doc_name)
        print("Chatbot Name: ", chatbot_name)

        # Create the upload directory if it doesn't exist
        upload_dir = os.path.join(MEDIA_ROOT, 'uploads', username, chatbot_name)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save the file
        file_path = os.path.join(upload_dir, doc_name)
        with open(file_path, "wb+") as destination:
            for chunk in document.chunks():
                destination.write(chunk)

        # Update MongoDB with the file path
        chatbots_collection.update_one(
            {'chatbot_name': chatbot_name},  # Assuming you have a field 'name' for chatbot
            {'$set': {'file_path': file_path}}  # Update the file_path field
        )

        return redirect('home')  # Redirect to a success page or wherever you want

    return render(request, "upload.html", {"chatbot_name": chatbot_name})

def view_uploads(request, chatbot_name):
    user = request.session.get("username")
    if not user:
        return redirect("login")

    # Fetch chatbot details from MongoDB
    chatbot_data = chatbots_collection.find_one({"username": user, "chatbot_name": chatbot_name})
    print("Chatbot Data: ", chatbot_data["chatbot_id"])
    if not chatbot_data:
        return render(request, "error.html", {"message": "Chatbot not found!"})

    # Get the chatbot's folder path
    chatbot_folder = os.path.join(MEDIA_ROOT, "uploads", user, chatbot_name)

    # List all files in the chatbot's folder 
    if os.path.exists(chatbot_folder):
        files = os.listdir(chatbot_folder)
        file_urls = []
        for file in files:
            file_urls.append({
                "name": file,
                "url": request.build_absolute_uri('/media/uploads/{}/{}/{}'.format(user, chatbot_name, file))
            })
        files = file_urls
    else:
        files = []

    return render(request, "view_uploads.html", {"chatbot_name": chatbot_name, "files": files, "user": user, "chatbot_id": chatbot_data['chatbot_id']})

def delete_document(request, chatbot_name, file_name):
    user = request.session.get("username")
    if not user:
        return redirect("login")

    # Fetch chatbot details from MongoDB
    chatbot_data = chatbots_collection.find_one({"username": user, "chatbot_name": chatbot_name})

    if not chatbot_data:
        return HttpResponse("Chatbot not found.", status=404)

    # Get the document's file path
    file_path = os.path.join(MEDIA_ROOT, "uploads", user, chatbot_name, file_name)

    # Delete the file from the file system
    if os.path.exists(file_path):
        os.remove(file_path)

    # Remove the file path from MongoDB
    chatbots_collection.update_one(
        {"username": user, "chatbot_name": chatbot_name},
        {"$unset": {"file_path": ""}}
    )

    # Redirect to the view_uploads view
    return redirect('view_uploads', chatbot_name=chatbot_name)


def chatbot_dashboard(request):
    # Render the template with the chatbots (empty or populated)
    return render(request, 'chatbot_dashboard.html')

def new_chatbot(request):
    if "username" not in request.session:
        return redirect("login")

    return render(request, 'new_chatbot.html')

def chatbot_detail(request, chatbot_id):
    chatbot = chatbots_collection.find_one({"chatbot_id": chatbot_id})

    if not chatbot:
        return render(request, "chatbot_detail.html", {"error": "Chatbot not found!"})

    return render(request, "chatbot_detail.html", {"chatbot": chatbot})

def send_verification_code(email, code):
    msg = MIMEText(f"Your verification code is: {code}")
    msg['Subject'] = 'Password Reset Verification Code'
    msg['From'] = 'your_email@example.com'
    msg['To'] = email

    with smtplib.SMTP('smtp.example.com', 587) as server:
        server.starttls()
        server.login('your_email@example.com', 'your_email_password')
        server.sendmail('your_email@example.com', email, msg.as_string())

def generate_verification_code(length=6):
    return ''.join(random.choice(string.digits) for i in range(length))

def forgot_password(request):
    if request.method == "POST":
        username = request.POST.get('username')
        user = users_collection.find_one({'username': username})
        if user:
            verification_code = generate_verification_code()
            users_collection.update_one({'username': username}, {'$set': {'verification_code': verification_code}})
            send_verification_code(user['email'], verification_code)
            return render(request, 'reset_password.html')
        else:
            return HttpResponse("Username not found!")
    return render(request, 'forgot_password.html')

def reset_password(request):
    if request.method == "POST":
        username = request.POST.get('username')
        verification_code = request.POST.get('verification_code')
        new_password = request.POST.get('new_password')
        user = users_collection.find_one({'username': username, 'verification_code': verification_code})
        if user:
            hashed_new_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            users_collection.update_one({'username': username}, {'$set': {'password': hashed_new_password, 'verification_code': None}})
            return HttpResponse("Password has been reset successfully!")
        else:
            return HttpResponse("Invalid verification code or username!")

def landingpage(request):
    # Render the template with the chatbots (empty or populated)
    return render(request, 'landingpage.html')

def chatbotView(request, chatbot_id):
    user = request.session.get("username")
    if not user:
        return redirect("login")

    chatbot = chatbots_collection.find_one({"chatbot_id": chatbot_id})

    if not chatbot:
        return render(request, "chatbot.html", {"error": "Chatbot not found!"})
    
    # Get the chatbot's folder path
    chatbot_folder = os.path.join(MEDIA_ROOT, "uploads", user, chatbot['chatbot_name'])

    # List all files in the chatbot's folder 
    if os.path.exists(chatbot_folder):
        files = os.listdir(chatbot_folder)
        file_urls = []
        for file in files:
            file_urls.append({
                "name": file,
                "url": '/media/uploads/{}/{}/{}'.format(user, chatbot['chatbot_name'], file)
            })
        files = file_urls
    else:
        files = []

    return render(request, "chatbot.html", {"chatbot": chatbot, "files": files[0]})

def get_response(request):
    if request.method == 'GET':
        user_input = request.GET.get('msg')
        text_file_path = os.path.join('C:/projects/ChatterMind_AI/chattermind'+ request.GET.get('text_file_path'))
        print(text_file_path)
        index_name = request.GET.get('index_name')
        chatbot = ChatBot()
        chatbot.setbot(text_file_path, index_name)  # Create an instance of your chatbot class
        response = chatbot.ask_question(user_input)
        print(response)
    return JsonResponse({'response':response})