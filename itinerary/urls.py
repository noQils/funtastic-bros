from django.urls import path
from . import views

app_name = 'itinerary'

urlpatterns = [
    path('', views.home, name='home'),
    path('create/', views.create_itinerary, name='create'),
    path('generate/', views.generate_itinerary, name='generate'),
    path('result/', views.itinerary_result, name='result'),
    path('detail/<int:itinerary_id>/', views.itinerary_detail, name='detail'),
    path('my-itineraries/', views.my_itineraries, name='my_itineraries'),
    path('saved/', views.saved_itineraries, name='saved'),
    path('save/<int:itinerary_id>/', views.save_itinerary, name='save'),
    path('<int:itinerary_id>/find-guides/', views.find_guides, name='find_guides'),
    path('explore/', views.explore_itineraries, name='explore'),
]
