from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse

from .models import TourGuide, Language, PersonalityTrait, GuideReview, Booking
from destinations.models import City, DestinationCategory

def guide_list(request):
    """List all verified guides with filtering"""
    guides = TourGuide.objects.filter(is_verified=True, is_available=True).select_related('user')
    
    # Filter by city
    city_id = request.GET.get('city')
    if city_id:
        guides = guides.filter(cities__id=city_id)
    
    # Filter by specialty
    specialty_id = request.GET.get('specialty')
    if specialty_id:
        guides = guides.filter(specialties__id=specialty_id)
    
    # Filter by language
    language_id = request.GET.get('language')
    if language_id:
        guides = guides.filter(languages__id=language_id)
    
    # Search by name
    search_query = request.GET.get('search', '')
    if search_query:
        guides = guides.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(bio__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(guides, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Filter options
    cities = City.objects.filter(is_active=True)
    specialties = DestinationCategory.objects.all()
    languages = Language.objects.all()
    
    context = {
        'page_obj': page_obj,
        'cities': cities,
        'specialties': specialties,
        'languages': languages,
        'selected_city': city_id,
        'selected_specialty': specialty_id,
        'selected_language': language_id,
        'search_query': search_query,
    }
    return render(request, 'guides/list.html', context)

def guide_profile(request, guide_id):
    """Display guide profile with reviews"""
    guide = get_object_or_404(
        TourGuide.objects.select_related('user').prefetch_related(
            'specialties', 'languages', 'personality_traits', 'cities'
        ), 
        id=guide_id, 
        is_verified=True
    )
    
    # Get recent reviews
    reviews = GuideReview.objects.filter(guide=guide, is_verified=True).select_related('reviewer')[:10]
    
    context = {
        'guide': guide,
        'reviews': reviews,
    }
    return render(request, 'guides/profile.html', context)

@login_required
def my_guide_profile(request):
    """Guide's own profile management"""
    if request.user.role != 'guider':
        messages.error(request, 'You need to be registered as a guide to access this page.')
        return redirect('guides:register')
    
    try:
        guide = request.user.guide_profile
    except TourGuide.DoesNotExist:
        messages.error(request, 'Please complete your guide profile setup.')
        return redirect('guides:edit_profile')
    
    # Get bookings and reviews
    bookings = Booking.objects.filter(guide=guide).select_related('tourist')[:10]
    reviews = GuideReview.objects.filter(guide=guide).select_related('reviewer')[:10]
    
    context = {
        'guide': guide,
        'bookings': bookings,
        'reviews': reviews,
    }
    return render(request, 'guides/my_profile.html', context)

@login_required
def edit_guide_profile(request):
    """Edit or create guide profile"""
    if request.user.role != 'guider':
        messages.error(request, 'You need to be registered as a guide to access this page.')
        return redirect('guides:register')
    
    try:
        guide = request.user.guide_profile
    except TourGuide.DoesNotExist:
        guide = None
    
    if request.method == 'POST':
        # Process form data
        bio = request.POST.get('bio', '')
        phone = request.POST.get('phone', '')
        years_of_experience = int(request.POST.get('years_of_experience', 0))
        hourly_rate = float(request.POST.get('hourly_rate', 0))
        daily_rate = float(request.POST.get('daily_rate', 0))
        profile_image = request.POST.get('profile_image', '')
        
        specialty_ids = request.POST.getlist('specialties')
        language_ids = request.POST.getlist('languages')
        trait_ids = request.POST.getlist('personality_traits')
        city_ids = request.POST.getlist('cities')
        
        if guide:
            # Update existing profile
            guide.bio = bio
            guide.phone = phone
            guide.years_of_experience = years_of_experience
            guide.hourly_rate = hourly_rate
            guide.daily_rate = daily_rate
            guide.profile_image = profile_image
            guide.save()
        else:
            # Create new profile
            guide = TourGuide.objects.create(
                user=request.user,
                bio=bio,
                phone=phone,
                years_of_experience=years_of_experience,
                hourly_rate=hourly_rate,
                daily_rate=daily_rate,
                profile_image=profile_image
            )
        
        # Update many-to-many relationships
        guide.specialties.set(specialty_ids)
        guide.languages.set(language_ids)
        guide.personality_traits.set(trait_ids)
        guide.cities.set(city_ids)
        
        messages.success(request, 'Your guide profile has been updated successfully!')
        return redirect('guides:my_profile')
    
    # Get form options
    specialties = DestinationCategory.objects.all()
    languages = Language.objects.all()
    traits = PersonalityTrait.objects.all()
    cities = City.objects.filter(is_active=True)
    
    context = {
        'guide': guide,
        'specialties': specialties,
        'languages': languages,
        'traits': traits,
        'cities': cities,
    }
    return render(request, 'guides/edit_profile.html', context)

@login_required
def register_as_guide(request):
    """Register user as a guide"""
    if request.user.role == 'guider':
        return redirect('guides:my_profile')
    
    if request.method == 'POST':
        # Update user role
        request.user.role = 'guider'
        request.user.save()
        
        messages.success(request, 'Welcome to the guide community! Please complete your profile.')
        return redirect('guides:edit_profile')
    
    return render(request, 'guides/register.html')

@login_required
def my_bookings(request):
    """Guide's booking management"""
    if request.user.role != 'guider':
        messages.error(request, 'Access denied.')
        return redirect('guides:list')
    
    try:
        guide = request.user.guide_profile
    except TourGuide.DoesNotExist:
        messages.error(request, 'Please complete your guide profile first.')
        return redirect('guides:edit_profile')
    
    bookings = Booking.objects.filter(guide=guide).select_related('tourist').order_by('-created_at')
    
    paginator = Paginator(bookings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'guides/my_bookings.html', context)

@login_required
def book_guide(request, guide_id):
    """Book a guide (placeholder - would integrate with booking system)"""
    guide = get_object_or_404(TourGuide, id=guide_id, is_verified=True, is_available=True)
    
    if request.method == 'POST':
        # This would integrate with a proper booking system
        # For MVP, just show a success message
        messages.success(request, f'Booking request sent to {guide.full_name}! They will contact you soon.')
        return redirect('guides:profile', guide_id=guide.id)
    
    context = {
        'guide': guide,
    }
    return render(request, 'guides/book.html', context)
