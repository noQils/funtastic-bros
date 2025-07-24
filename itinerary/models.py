from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from destinations.models import City, Destination
from guides.models import TourGuide
import json

User = get_user_model()

class TravelInterest(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    keywords = models.CharField(max_length=200, help_text="Comma-separated keywords for AI matching")

    def __str__(self):
        return self.name


class Itinerary(models.Model):
    BUDGET_RANGE_CHOICES = [
        ('budget', 'Budget (< 500K IDR/day)'),
        ('mid-range', 'Mid-range (500K - 1.5M IDR/day)'),
        ('luxury', 'Luxury (> 1.5M IDR/day)'),
    ]

    # User and basic info
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='itineraries')
    title = models.CharField(max_length=200)
    
    # Trip parameters
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='itineraries')
    interests = models.ManyToManyField(TravelInterest, related_name='itineraries')
    budget_range = models.CharField(max_length=20, choices=BUDGET_RANGE_CHOICES)
    duration_days = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(30)])
    
    # Trip dates
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # AI Generation details
    ai_prompt_used = models.TextField(help_text="The prompt sent to AI for generation")
    ai_response_raw = models.JSONField(default=dict, help_text="Raw AI response")
    
    # Estimated costs
    estimated_total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estimated_daily_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Status
    is_favorite = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.city.name} ({self.duration_days} days)"

    @property
    def total_activities(self):
        return self.days.aggregate(
            total=models.Sum('activities__id', distinct=True)
        )['total'] or 0


class ItineraryDay(models.Model):
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='days')
    day_number = models.IntegerField(validators=[MinValueValidator(1)])
    title = models.CharField(max_length=200, help_text="e.g., 'Day 1: Cultural Exploration'")
    description = models.TextField(blank=True)
    estimated_daily_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['day_number']
        unique_together = ['itinerary', 'day_number']

    def __str__(self):
        return f"{self.itinerary.title} - Day {self.day_number}"


class ItineraryActivity(models.Model):
    ACTIVITY_TYPE_CHOICES = [
        ('destination', 'Visit Destination'),
        ('meal', 'Meal/Restaurant'),
        ('transport', 'Transportation'),
        ('rest', 'Rest/Break'),
        ('shopping', 'Shopping'),
        ('other', 'Other Activity'),
    ]

    day = models.ForeignKey(ItineraryDay, on_delete=models.CASCADE, related_name='activities')
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, null=True, blank=True)
    
    # Activity details
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPE_CHOICES, default='destination')
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Timing
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration_minutes = models.IntegerField()
    
    # Costs
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Location (for non-destination activities)
    custom_location = models.CharField(max_length=200, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Ordering
    order = models.IntegerField(default=0)
    
    # Notes and tips
    ai_notes = models.TextField(blank=True, help_text="AI-generated tips for this activity")
    user_notes = models.TextField(blank=True, help_text="User's personal notes")

    class Meta:
        ordering = ['order', 'start_time']

    def __str__(self):
        return f"{self.day} - {self.title} ({self.start_time})"

    @property
    def location_name(self):
        if self.destination:
            return self.destination.name
        return self.custom_location or "Unknown Location"


class SavedItinerary(models.Model):
    """Users can save itineraries from other users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_itineraries')
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'itinerary']

    def __str__(self):
        return f"{self.user.username} saved {self.itinerary.title}"


class ItineraryGuideRequest(models.Model):
    """Connect itineraries with guide requests"""
    REQUEST_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('matched', 'Matched'),
        ('booked', 'Booked'),
        ('cancelled', 'Cancelled'),
    ]

    itinerary = models.OneToOneField(Itinerary, on_delete=models.CASCADE, related_name='guide_request')
    preferred_guide = models.ForeignKey(TourGuide, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Preferences
    preferred_personality_traits = models.CharField(max_length=200, blank=True)
    preferred_languages = models.CharField(max_length=100, blank=True)
    max_budget_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status
    status = models.CharField(max_length=20, choices=REQUEST_STATUS_CHOICES, default='pending')
    matched_guides = models.ManyToManyField(TourGuide, related_name='potential_matches', blank=True)
    
    # AI matching data
    ai_matching_scores = models.JSONField(default=dict, help_text="Guide ID -> matching score")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Guide request for {self.itinerary.title}"
