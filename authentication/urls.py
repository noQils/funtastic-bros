from django.urls import path
from .views import (
    login_user, register_user, logout_user, show_main,
    tour_guides_list, tour_guide_profile, rate_tour_guide
)

app_name = 'authentication'

urlpatterns = [
    path('login/', login_user, name='login'),
    path('register/', register_user, name='register'),
    path('logout/', logout_user, name='logout'),
    path('main/', show_main, name='show_main'),
    path('tour-guides/', tour_guides_list, name='tour_guides_list'),
    path('tour-guide/<int:user_id>/', tour_guide_profile, name='tour_guide_profile'),
    path('rate/<int:user_id>/', rate_tour_guide, name='rate_tour_guide'),
]