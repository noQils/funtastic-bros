from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q

from .models import City, Destination, DestinationCategory, DestinationReview

def destination_list(request):
    """List all destinations with filtering"""
    destinations = Destination.objects.filter(is_active=True).select_related('city', 'category')
    
    # Filter by city
    city_id = request.GET.get('city')
    if city_id:
        destinations = destinations.filter(city_id=city_id)
    
    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        destinations = destinations.filter(category_id=category_id)
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        destinations = destinations.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(address__icontains=search_query)
        )
    
    # Sort by
    sort_by = request.GET.get('sort', 'popularity')
    if sort_by == 'rating':
        destinations = destinations.order_by('-rating', '-popularity_score')
    elif sort_by == 'price_low':
        destinations = destinations.order_by('average_cost')
    elif sort_by == 'price_high':
        destinations = destinations.order_by('-average_cost')
    else:  # default: popularity
        destinations = destinations.order_by('-popularity_score', '-rating')
    
    # Pagination
    paginator = Paginator(destinations, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Filter options
    cities = City.objects.filter(is_active=True)
    categories = DestinationCategory.objects.all()
    
    context = {
        'page_obj': page_obj,
        'cities': cities,
        'categories': categories,
        'selected_city': city_id,
        'selected_category': category_id,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    return render(request, 'destinations/list.html', context)

def destination_detail(request, destination_id):
    """Display destination details with reviews"""
    destination = get_object_or_404(
        Destination.objects.select_related('city', 'category').prefetch_related('images'), 
        id=destination_id, 
        is_active=True
    )
    
    # Get reviews
    reviews = DestinationReview.objects.filter(destination=destination).order_by('-created_at')[:10]
    
    # Get related destinations (same category, same city)
    related_destinations = Destination.objects.filter(
        city=destination.city,
        category=destination.category,
        is_active=True
    ).exclude(id=destination.id)[:6]
    
    context = {
        'destination': destination,
        'reviews': reviews,
        'related_destinations': related_destinations,
    }
    return render(request, 'destinations/detail.html', context)

def city_destinations(request, city_id):
    """List destinations for a specific city"""
    city = get_object_or_404(City, id=city_id, is_active=True)
    destinations = Destination.objects.filter(
        city=city, 
        is_active=True
    ).select_related('category').order_by('-popularity_score', '-rating')
    
    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        destinations = destinations.filter(category_id=category_id)
    
    # Pagination
    paginator = Paginator(destinations, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Categories for this city
    categories = DestinationCategory.objects.filter(
        destinations__city=city,
        destinations__is_active=True
    ).distinct()
    
    context = {
        'city': city,
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': category_id,
    }
    return render(request, 'destinations/city_destinations.html', context)
