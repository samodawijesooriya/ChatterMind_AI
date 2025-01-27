from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import User
from django.contrib import messages

def login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = User.objects.filter(username=username, password=password).first()
        if user:
            return HttpResponse("Login successful!")
        else:
            messages.error(request, "Invalid credentials!")
    return render(request, 'users/login.html')

def register(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
        else:
            user = User(username=username, password=password)
            user.save()
            messages.success(request, "Registration successful!")
            return redirect('login')
    return render(request, 'users/register.html')