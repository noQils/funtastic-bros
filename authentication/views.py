from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
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
from .forms import CustomUserCreationForm, TourGuideRatingForm
from .models import User, TourGuideRating
from django.db import transaction
from destinations.models import City, Destination

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
    
    response = HttpResponseRedirect(reverse('authentication:login'))
    response.delete_cookie('last_login')

    return response

def show_main(request):
    # Get all cities for the main page
    cities = City.objects.filter(is_active=True)
    
    if request.user.is_authenticated:
        username = request.user.username
        last_login = request.COOKIES.get('last_login', 'No login recorded')
    else:
        username = None
        last_login = None

    context = {
        'username': username,
        'last_login': last_login,
        'cities': cities
    }

    return render(request, 'show_main.html', context)

def city_destinations(request, city_id):
    """Display all destinations for a specific city"""
    city = get_object_or_404(City, id=city_id, is_active=True)
    destinations = Destination.objects.filter(city=city, is_active=True).select_related('category')
    
    context = {
        'city': city,
        'destinations': destinations
    }
    
    return render(request, 'city_destinations.html', context)


def tour_guides_list(request):
    """View to show all tour guides"""
    tour_guides = User.objects.filter(role='guider').order_by('-total_ratings', 'username')
    
    context = {
        'tour_guides': tour_guides
    }
    
    return render(request, 'tour_guides_list.html', context)


def tour_guide_profile(request, user_id):
    """View to show individual tour guide profile with ratings"""
    tour_guide = get_object_or_404(User, id=user_id, role='guider')
    
    # Check if current user has already rated this tour guide
    existing_rating = None
    if request.user.is_authenticated and request.user.role == 'user':
        try:
            existing_rating = TourGuideRating.objects.get(
                rater=request.user, 
                tour_guide=tour_guide
            )
        except TourGuideRating.DoesNotExist:
            pass
    
    context = {
        'tour_guide': tour_guide,
        'existing_rating': existing_rating,
        'can_rate': (request.user.is_authenticated and 
                    request.user.role == 'user' and 
                    request.user != tour_guide)
    }
    
    return render(request, 'tour_guide_profile.html', context)


@login_required
def rate_tour_guide(request, user_id):
    """View to rate a tour guide"""
    tour_guide = get_object_or_404(User, id=user_id, role='guider')
    
    # Check if user can rate (must be a user, not the tour guide themselves)
    if request.user.role != 'user' or request.user == tour_guide:
        messages.error(request, 'You are not allowed to rate this tour guide.')
        return redirect('authentication:tour_guide_profile', user_id=user_id)
    
    # Get or create rating
    rating, created = TourGuideRating.objects.get_or_create(
        rater=request.user,
        tour_guide=tour_guide
    )
    
    if request.method == 'POST':
        print(f"POST data: {request.POST}")
        form = TourGuideRatingForm(request.POST, instance=rating)
        print(f"Form is valid: {form.is_valid()}")
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
        
        if form.is_valid():
            with transaction.atomic():
                # Save new rating first
                new_rating = form.save(commit=False)
                new_rating.rater = request.user
                new_rating.tour_guide = tour_guide
                new_rating.save()
                
                # Debug: print the saved rating values
                print(f"Saved rating: ramah={new_rating.ramah}, seru={new_rating.seru}, informatif={new_rating.informatif}, fleksibel={new_rating.fleksibel}, easy_going={new_rating.easy_going}")
                
                # Update tour guide's rating counts
                update_tour_guide_ratings(tour_guide, created)
                
                messages.success(request, f'Thank you for rating {tour_guide.username}!')
                return redirect('authentication:tour_guide_profile', user_id=user_id)
    else:
        form = TourGuideRatingForm(instance=rating)
    
    context = {
        'form': form,
        'tour_guide': tour_guide,
        'rating': rating,
        'is_edit': not created
    }
    
    return render(request, 'rate_tour_guide.html', context)


def update_tour_guide_ratings(tour_guide, is_new_rating):
    """Recalculate tour guide's rating counts from all ratings"""
    
    # Get all ratings for this tour guide
    all_ratings = TourGuideRating.objects.filter(tour_guide=tour_guide)
    
    # Reset all counts
    tour_guide.total_ratings = all_ratings.count()
    tour_guide.ramah_count = all_ratings.filter(ramah=True).count()
    tour_guide.seru_count = all_ratings.filter(seru=True).count()
    tour_guide.informatif_count = all_ratings.filter(informatif=True).count()
    tour_guide.fleksibel_count = all_ratings.filter(fleksibel=True).count()
    tour_guide.easy_going_count = all_ratings.filter(easy_going=True).count()
    
    tour_guide.save()
    
    print(f"Updated {tour_guide.username}: total_ratings={tour_guide.total_ratings}, ramah={tour_guide.ramah_count}, seru={tour_guide.seru_count}, informatif={tour_guide.informatif_count}, fleksibel={tour_guide.fleksibel_count}, easy_going={tour_guide.easy_going_count}")