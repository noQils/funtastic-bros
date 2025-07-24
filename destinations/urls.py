from django.urls import path
from . import views

app_name = 'destinations'

urlpatterns = [
    path('', views.destination_list, name='list'),
    path('<int:destination_id>/', views.destination_detail, name='detail'),
    path('city/<int:city_id>/', views.city_destinations, name='city_destinations'),
]
