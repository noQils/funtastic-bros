from django.urls import path
from .views import login_user, register_user, logout_user, show_main

app_name = 'authentication'

urlpatterns = [
    path('login/', login_user, name='login'),
    path('register/', register_user, name='register'),
    path('logout/', logout_user, name='logout'),
    path('main/', show_main, name='show_main'),
]