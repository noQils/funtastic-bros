from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
import json
import re
from datetime import datetime, timedelta

from .models import (
    TravelInterest, Itinerary, ItineraryDay, ItineraryActivity, 
    SavedItinerary, ItineraryGuideRequest
)
from destinations.models import City, Destination
from guides.models import TourGuide
from .ai_service import AIItineraryService

def extract_cost_value(cost_string):
    """Extract numeric value from cost strings like 'IDR 2,450,000' or 'IDR 500,000'"""
    if not cost_string:
        return 0
    
    # Remove currency symbols, commas, and extract numbers
    numeric_part = re.sub(r'[^\d.]', '', str(cost_string))
    
    try:
        return float(numeric_part) if numeric_part else 0
    except ValueError:
        return 0

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

def create_itinerary(request):
    """Display the itinerary creation form"""
    cities = City.objects.filter(is_active=True)
    interests = TravelInterest.objects.all()
    
    context = {
        'cities': cities,
        'interests': interests,
    }
    return render(request, 'itinerary/create.html', context)

@require_http_methods(["POST"])
def generate_itinerary(request):
    """Generate an itinerary using AI"""
    try:
        # Get form data
        city_id = request.POST.get('city')
        budget_range = request.POST.get('budget_range')
        duration_days = int(request.POST.get('duration_days', 3))
        start_date = request.POST.get('start_date')
        travel_style = request.POST.get('travel_style', 'relaxed')
        interests = request.POST.getlist('interests')
        additional_preferences = request.POST.get('additional_preferences', '')

        # Validate required fields
        if not all([city_id, budget_range, duration_days, start_date]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('itinerary:create')

        # Get city and interest objects
        city = get_object_or_404(City, id=city_id)
        interest_objects = TravelInterest.objects.filter(id__in=interests)
        interest_names = [interest.name for interest in interest_objects]

        # Get destinations for this city
        destinations = Destination.objects.filter(city=city, is_active=True)
        destinations_data = []
        for dest in destinations:
            destinations_data.append({
                'id': dest.id,
                'name': dest.name,
                'description': dest.description,
                'category': dest.category.name,
                'price': float(dest.average_cost),
                'rating': float(dest.rating),
                'time_minutes': float(dest.estimated_duration_hours * 60),
            })

        # Initialize AI service and generate itinerary
        ai_service = AIItineraryService()
        result = ai_service.generate_itinerary(
            city=city.name,
            interests=interest_names,
            budget_range=budget_range,
            duration_days=duration_days,
            travel_style=travel_style,
            additional_preferences=additional_preferences,
            available_destinations=destinations_data
        )

        if result['success']:
            # Store the result in session for the result page
            request.session['itinerary_result'] = {
                'itinerary': result['itinerary'],
                'city': city.name,
                'city_id': city.id,
                'budget_range': budget_range,
                'duration_days': duration_days,
                'travel_style': travel_style,
                'interests': interest_names,
                'destinations_used': result.get('destinations_used', []),
                'rag_enabled': result.get('rag_enabled', False),
                'practical_info': result.get('practical_info', {}),
                'ai_response_raw': result.get('ai_response_raw', ''),
            }
            return redirect('itinerary:result')
        else:
            messages.error(request, 'Failed to generate itinerary. Please try again.')
            return redirect('itinerary:create')

    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('itinerary:create')

def itinerary_result(request):
    """Display the generated itinerary result"""
    itinerary_data = request.session.get('itinerary_result')
    
    if not itinerary_data:
        messages.error(request, 'No itinerary data found. Please generate a new itinerary.')
        return redirect('itinerary:create')
    
    context = {
        'itinerary': itinerary_data['itinerary'],
        'city': itinerary_data['city'],
        'destinations_used': itinerary_data.get('destinations_used', []),
        'rag_enabled': itinerary_data.get('rag_enabled', False),
        'practical_info': itinerary_data.get('practical_info', {}),
        'debug': True,  # Set to False in production
    }
    
    return render(request, 'itinerary/result.html', context)

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
        
        # Extract numeric values from cost strings
        total_cost_str = result['itinerary'].get('total_estimated_cost', '0')
        daily_cost_str = result['itinerary'].get('daily_cost', total_cost_str)
        
        total_cost = extract_cost_value(total_cost_str)
        daily_cost = extract_cost_value(daily_cost_str)
        
        # If daily cost is not available, calculate from total
        if daily_cost == 0 and total_cost > 0:
            daily_cost = total_cost / duration_days
        
        # Create itinerary in database
        itinerary = Itinerary.objects.create(
            user=request.user,
            title=result['itinerary']['title'],
            city=city,
            budget_range=budget_range,
            duration_days=duration_days,
            start_date=datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None,
            end_date=datetime.strptime(start_date, '%Y-%m-%d').date() + timedelta(days=duration_days-1) if start_date else None,
            ai_prompt_used=result.get('prompt_used', ''),
            ai_response_raw=result.get('ai_response_raw', ''),
            estimated_total_cost=total_cost,
            estimated_daily_cost=daily_cost,
        )
        
        # Add interests
        itinerary.interests.set(interests)
        
        # Create itinerary days and activities
        for day_data in result['itinerary']['days']:
            # Extract daily cost
            daily_cost_value = extract_cost_value(day_data.get('daily_total', '0'))
            
            itinerary_day = ItineraryDay.objects.create(
                itinerary=itinerary,
                day_number=day_data['day'],
                title=day_data.get('theme', f"Day {day_data['day']}"),
                estimated_daily_cost=daily_cost_value
            )
            
            for i, activity_data in enumerate(day_data['activities']):
                # Find destination if specified
                destination = None
                if activity_data.get('location'):
                    destination = destinations.filter(
                        name__icontains=activity_data['location']
                    ).first()
                
                # Parse time
                try:
                    time_range = activity_data.get('time', '09:00 AM - 10:00 AM')
                    if ' - ' in time_range:
                        start_time_str = time_range.split(' - ')[0].strip()
                        # Handle AM/PM format
                        if 'AM' in start_time_str or 'PM' in start_time_str:
                            start_time = datetime.strptime(start_time_str, '%I:%M %p').time()
                        else:
                            start_time = datetime.strptime(start_time_str, '%H:%M').time()
                    else:
                        start_time = datetime.strptime('09:00', '%H:%M').time()
                    
                    duration_minutes = 120  # Default 2 hours
                    start_datetime = datetime.combine(datetime.today(), start_time)
                    end_datetime = start_datetime + timedelta(minutes=duration_minutes)
                    end_time = end_datetime.time()
                except:
                    start_time = datetime.strptime('09:00', '%H:%M').time()
                    end_time = datetime.strptime('11:00', '%H:%M').time()
                    duration_minutes = 120
                
                # Extract activity cost
                activity_cost = extract_cost_value(activity_data.get('cost', '0'))
                
                ItineraryActivity.objects.create(
                    day=itinerary_day,
                    destination=destination,
                    activity_type=activity_data.get('type', 'activity'),
                    title=activity_data.get('activity', activity_data.get('title', 'Activity')),
                    description=activity_data.get('description', ''),
                    start_time=start_time,
                    end_time=end_time,
                    duration_minutes=duration_minutes,
                    estimated_cost=activity_cost,
                    custom_location=activity_data.get('location', '') if not destination else '',
                    order=i,
                    ai_notes=activity_data.get('tips', '')
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
