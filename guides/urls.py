from django.urls import path
from . import views

app_name = 'guides'

urlpatterns = [
    path('', views.guide_list, name='list'),
    path('profile/<int:guide_id>/', views.guide_profile, name='profile'),
    path('my-profile/', views.my_guide_profile, name='my_profile'),
    path('edit-profile/', views.edit_guide_profile, name='edit_profile'),
    path('register/', views.register_as_guide, name='register'),
    path('bookings/', views.my_bookings, name='bookings'),
    path('book/<int:guide_id>/', views.book_guide, name='book'),
]
