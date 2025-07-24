from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.core import serializers
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.shortcuts import reverse
import datetime
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.html import strip_tags
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from .forms import CustomUserCreationForm

def register_user(request):
    form = CustomUserCreationForm()

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, 'Your account has been successfully created!')
            
            return redirect('authentication:login')
    
    context = {'form':form}
    
    return render(request, 'register.html', context)

def login_user(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)

            response = HttpResponseRedirect(reverse("authentication:show_main"))
            response.set_cookie('last_login', str(datetime.datetime.now()))

            return response
        
        else:
            messages.error(request, 'Wrong username or password')

    else:
        form = AuthenticationForm(request)

    context = {'form': form}
    
    return render(request, 'login.html', context)

@login_required
def logout_user(request):
    username = request.user.username

    logout(request)
    
    response = HttpResponseRedirect(reverse('root'))
    response.delete_cookie('last_login')

    return response

def show_main(request):
    if request.user.is_authenticated:
        username = request.user.username
        last_login = request.COOKIES.get('last_login', 'No login recorded')
    else:
        username = None
        last_login = None

    context = {
        'username': username,
        'last_login': last_login
    }

    return render(request, 'show_main.html', context)