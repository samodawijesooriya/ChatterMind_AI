from django.shortcuts import render
from django.http import HttpResponse


def login(request):
    if request.method == "POST":
        print(request.POST)
        username = request.POST.get('username')
        password = request.POST.get('password')
        # Add authentication logic here
        if username == "admin" and password == "password":  # Example check
            return HttpResponse("Login successful!")
        else:
            return HttpResponse("Invalid credentials!")
    return render(request, 'login.html')