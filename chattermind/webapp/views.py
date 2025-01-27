from django.shortcuts import render
from django.http import HttpResponse
from pymongo import MongoClient
import bcrypt

client = MongoClient("mongodb+srv://798white:SgOe9IxCwPEZIx1L@chatterbot.zv9ev.mongodb.net/?retryWrites=true&w=majority&appName=chatterbot")
db = client.get_database('chatterbot')
users_collection = db.get_collection('users')

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