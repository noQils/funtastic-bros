from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
import json
from datetime import datetime, timedelta

from .models import (
    TravelInterest, Itinerary, ItineraryDay, ItineraryActivity, 
    SavedItinerary, ItineraryGuideRequest
)
from destinations.models import City, Destination
from guides.models import TourGuide
from .ai_service import AIItineraryService

def home(request):
    """Home page with itinerary generation form"""
    cities = City.objects.filter(is_active=True)
    interests = TravelInterest.objects.all()
    featured_itineraries = Itinerary.objects.filter(is_public=True)[:6]
    
    context = {
        'cities': cities,
        'interests': interests,
        'featured_itineraries': featured_itineraries,
    }
    return render(request, 'itinerary/home.html', context)

@login_required
@require_http_methods(["POST"])
def generate_itinerary(request):
    """Generate AI-powered itinerary"""
    try:
        # Get form data
        city_id = request.POST.get('city')
        interest_ids = request.POST.getlist('interests')
        budget_range = request.POST.get('budget_range')
        duration_days = int(request.POST.get('duration_days', 3))
        start_date = request.POST.get('start_date')
        
        # Validate inputs
        if not all([city_id, interest_ids, budget_range, duration_days]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('itinerary:home')
        
        # Get database objects
        city = get_object_or_404(City, id=city_id, is_active=True)
        interests = TravelInterest.objects.filter(id__in=interest_ids)
        
        # Get available destinations for the city
        destinations = Destination.objects.filter(
            city=city, 
            is_active=True
        ).select_related('category')
        
        # Prepare destinations data for AI
        destinations_data = []
        for dest in destinations:
            destinations_data.append({
                'name': dest.name,
                'description': dest.description,
                'category': dest.category.name,
                'address': dest.address,
                'average_cost': float(dest.average_cost),
                'estimated_duration_hours': float(dest.estimated_duration_hours),
                'rating': float(dest.rating),
                'opening_hours': dest.opening_hours,
                'best_time_to_visit': dest.best_time_to_visit,
            })
        
        # Generate itinerary using AI
        ai_service = AIItineraryService()
        result = ai_service.generate_itinerary(
            city=city.name,
            interests=[interest.name for interest in interests],
            budget_range=budget_range,
            duration_days=duration_days,
            available_destinations=destinations_data
        )
        
        if not result['success']:
            messages.error(request, 'Failed to generate itinerary. Please try again.')
            return redirect('itinerary:home')
        
        # Create itinerary in database
        itinerary = Itinerary.objects.create(
            user=request.user,
            title=result['itinerary']['title'],
            city=city,
            budget_range=budget_range,
            duration_days=duration_days,
            start_date=datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None,
            end_date=datetime.strptime(start_date, '%Y-%m-%d').date() + timedelta(days=duration_days-1) if start_date else None,
            ai_prompt_used=result['prompt_used'],
            ai_response_raw=result['ai_response_raw'],
            estimated_total_cost=result['itinerary']['total_estimated_cost'],
            estimated_daily_cost=result['itinerary']['daily_cost'],
        )
        
        # Add interests
        itinerary.interests.set(interests)
        
        # Create itinerary days and activities
        for day_data in result['itinerary']['days']:
            itinerary_day = ItineraryDay.objects.create(
                itinerary=itinerary,
                day_number=day_data['day_number'],
                title=day_data['title'],
                estimated_daily_cost=day_data.get('daily_cost', 0)
            )
            
            for i, activity_data in enumerate(day_data['activities']):
                # Find destination if specified
                destination = None
                if activity_data.get('destination_name'):
                    destination = destinations.filter(
                        name__icontains=activity_data['destination_name']
                    ).first()
                
                # Parse time
                try:
                    start_time = datetime.strptime(activity_data['time'], '%H:%M').time()
                    duration_minutes = activity_data['duration_minutes']
                    start_datetime = datetime.combine(datetime.today(), start_time)
                    end_datetime = start_datetime + timedelta(minutes=duration_minutes)
                    end_time = end_datetime.time()
                except:
                    start_time = datetime.strptime('09:00', '%H:%M').time()
                    end_time = datetime.strptime('10:00', '%H:%M').time()
                    duration_minutes = 60
                
                ItineraryActivity.objects.create(
                    day=itinerary_day,
                    destination=destination,
                    activity_type=activity_data.get('type', 'destination'),
                    title=activity_data['title'],
                    description=activity_data.get('description', ''),
                    start_time=start_time,
                    end_time=end_time,
                    duration_minutes=duration_minutes,
                    estimated_cost=activity_data.get('estimated_cost', 0),
                    custom_location=activity_data.get('destination_name', '') if not destination else '',
                    order=i,
                    ai_notes=activity_data.get('notes', '')
                )
        
        messages.success(request, 'Your personalized itinerary has been generated!')
        return redirect('itinerary:detail', itinerary_id=itinerary.id)
        
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('itinerary:home')

@login_required
def itinerary_detail(request, itinerary_id):
    """Display detailed itinerary"""
    itinerary = get_object_or_404(
        Itinerary.objects.prefetch_related(
            'days__activities__destination',
            'interests'
        ), 
        id=itinerary_id
    )
    
    # Check if user owns the itinerary or it's public
    if itinerary.user != request.user and not itinerary.is_public:
        messages.error(request, 'You do not have permission to view this itinerary.')
        return redirect('itinerary:home')
    
    # Check if user has saved this itinerary
    is_saved = False
    if request.user.is_authenticated and itinerary.user != request.user:
        is_saved = SavedItinerary.objects.filter(
            user=request.user, 
            itinerary=itinerary
        ).exists()
    
    # Get available guides for this itinerary
    available_guides = TourGuide.objects.filter(
        cities=itinerary.city,
        is_available=True,
        is_verified=True
    ).select_related('user').prefetch_related(
        'specialties', 'languages', 'personality_traits'
    )[:6]
    
    context = {
        'itinerary': itinerary,
        'is_saved': is_saved,
        'available_guides': available_guides,
    }
    return render(request, 'itinerary/detail.html', context)

@login_required
def my_itineraries(request):
    """Display user's itineraries"""
    itineraries = Itinerary.objects.filter(user=request.user).prefetch_related('interests')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        itineraries = itineraries.filter(
            Q(title__icontains=search_query) |
            Q(city__name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(itineraries, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'itinerary/my_itineraries.html', context)

@login_required
def saved_itineraries(request):
    """Display user's saved itineraries"""
    saved = SavedItinerary.objects.filter(user=request.user).select_related(
        'itinerary__city', 'itinerary__user'
    ).prefetch_related('itinerary__interests')
    
    paginator = Paginator(saved, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'itinerary/saved_itineraries.html', context)

@login_required
@require_http_methods(["POST"])
def save_itinerary(request, itinerary_id):
    """Save/unsave an itinerary"""
    itinerary = get_object_or_404(Itinerary, id=itinerary_id, is_public=True)
    
    if itinerary.user == request.user:
        return JsonResponse({'error': 'Cannot save your own itinerary'}, status=400)
    
    saved_obj, created = SavedItinerary.objects.get_or_create(
        user=request.user,
        itinerary=itinerary
    )
    
    if not created:
        saved_obj.delete()
        return JsonResponse({'saved': False, 'message': 'Itinerary removed from saved list'})
    
    return JsonResponse({'saved': True, 'message': 'Itinerary saved successfully'})

@login_required
def find_guides(request, itinerary_id):
    """Find and match guides for an itinerary"""
    itinerary = get_object_or_404(Itinerary, id=itinerary_id, user=request.user)
    
    # Get all available guides for the city
    available_guides = TourGuide.objects.filter(
        cities=itinerary.city,
        is_available=True,
        is_verified=True
    ).select_related('user').prefetch_related(
        'specialties', 'languages', 'personality_traits'
    )
    
    # Prepare guides data for AI matching
    guides_data = []
    for guide in available_guides:
        guides_data.append({
            'id': guide.id,
            'name': guide.full_name,
            'bio': guide.bio,
            'years_of_experience': guide.years_of_experience,
            'specialties': [s.name for s in guide.specialties.all()],
            'languages': [l.name for l in guide.languages.all()],
            'personality_traits': [p.name for p in guide.personality_traits.all()],
            'hourly_rate': float(guide.hourly_rate),
            'daily_rate': float(guide.daily_rate),
            'average_rating': float(guide.average_rating),
            'total_reviews': guide.total_reviews,
            'is_available': guide.is_available,
        })
    
    # Use AI to match guides
    ai_service = AIItineraryService()
    itinerary_data = {
        'interests': [interest.name for interest in itinerary.interests.all()],
        'budget_range': itinerary.budget_range,
        'duration_days': itinerary.duration_days,
    }
    
    matched_guides = ai_service.match_guide_to_itinerary(itinerary_data, guides_data)
    
    # Get TourGuide objects for matched guides
    matched_guide_ids = [g['id'] for g in matched_guides]
    guide_objects = {g.id: g for g in available_guides.filter(id__in=matched_guide_ids)}
    
    # Combine AI matching data with guide objects
    for guide_match in matched_guides:
        guide_match['guide_object'] = guide_objects.get(guide_match['id'])
    
    context = {
        'itinerary': itinerary,
        'matched_guides': matched_guides,
    }
    return render(request, 'itinerary/find_guides.html', context)

def explore_itineraries(request):
    """Browse public itineraries"""
    itineraries = Itinerary.objects.filter(is_public=True).select_related(
        'user', 'city'
    ).prefetch_related('interests')
    
    # Filter by city
    city_id = request.GET.get('city')
    if city_id:
        itineraries = itineraries.filter(city_id=city_id)
    
    # Filter by interests
    interest_ids = request.GET.getlist('interests')
    if interest_ids:
        itineraries = itineraries.filter(interests__id__in=interest_ids).distinct()
    
    # Filter by budget range
    budget_range = request.GET.get('budget_range')
    if budget_range:
        itineraries = itineraries.filter(budget_range=budget_range)
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        itineraries = itineraries.filter(
            Q(title__icontains=search_query) |
            Q(city__name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(itineraries, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Filter options
    cities = City.objects.filter(is_active=True)
    interests = TravelInterest.objects.all()
    
    context = {
        'page_obj': page_obj,
        'cities': cities,
        'interests': interests,
        'selected_city': city_id,
        'selected_interests': interest_ids,
        'selected_budget': budget_range,
        'search_query': search_query,
    }
    return render(request, 'itinerary/explore.html', context)
