from django.shortcuts import render
from django.http import HttpResponse

def signin(request):
    return render(request, 'main/signin.html')

def home(request):
    return render(request, 'main/home.html')

def gamemodes(request):
    return render(request, 'main/gamemodes.html')
