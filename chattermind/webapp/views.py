from django.shortcuts import render, redirect
from django.http import  HttpResponse, JsonResponse
from pymongo import MongoClient
import bcrypt

client = MongoClient("mongodb+srv://798white:SgOe9IxCwPEZIx1L@chatterbot.zv9ev.mongodb.net/?retryWrites=true&w=majority&appName=chatterbot")
db = client.get_database('chatterbot')
users_collection = db.get_collection('users')

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
            
            request.session['username'] = username
            request.session['dark_mode'] = False  # Default light mode
            return redirect('settings')  # Redirect to settings after login
        else:
            return HttpResponse("Invalid credentials!")
    return render(request, 'login.html')