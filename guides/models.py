from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from destinations.models import City, DestinationCategory

User = get_user_model()

class Language(models.Model):
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=5, unique=True)  # e.g., 'en', 'id'

    def __str__(self):
        return self.name


class PersonalityTrait(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class TourGuide(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='guide_profile')
    
    # Basic Info
    bio = models.TextField(help_text="Tell tourists about yourself and your guiding experience")
    profile_image = models.URLField(blank=True, help_text="Profile photo URL")
    phone = models.CharField(max_length=20)
    
    # Professional Details
    years_of_experience = models.IntegerField(validators=[MinValueValidator(0)])
    specialties = models.ManyToManyField(DestinationCategory, related_name='specialized_guides')
    languages = models.ManyToManyField(Language, related_name='guides')
    personality_traits = models.ManyToManyField(PersonalityTrait, related_name='guides')
    
    # Service Areas
    cities = models.ManyToManyField(City, related_name='available_guides')
    
    # Pricing
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price per hour in IDR")
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price per day in IDR")
    
    # Ratings and Reviews
    average_rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    total_reviews = models.IntegerField(default=0)
    total_tours = models.IntegerField(default=0)
    
    # Availability
    is_available = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-average_rating', '-total_reviews']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - Guide"

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username


class GuideAvailability(models.Model):
    guide = models.ForeignKey(TourGuide, on_delete=models.CASCADE, related_name='availability')
    date = models.DateField()
    is_available = models.BooleanField(default=True)
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ['guide', 'date']
        ordering = ['date']

    def __str__(self):
        return f"{self.guide.full_name} - {self.date} ({'Available' if self.is_available else 'Unavailable'})"


class GuideReview(models.Model):
    guide = models.ForeignKey(TourGuide, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_guide_reviews')
    
    # Review details
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=100)
    comment = models.TextField()
    
    # Trip details
    tour_date = models.DateField()
    destinations_visited = models.CharField(max_length=500, help_text="Comma-separated list of places visited")
    
    # Review metadata
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['guide', 'reviewer', 'tour_date']

    def __str__(self):
        return f"{self.reviewer.username} -> {self.guide.full_name} ({self.rating}/5)"


class Booking(models.Model):
    BOOKING_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    # Parties involved
    tourist = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    guide = models.ForeignKey(TourGuide, on_delete=models.CASCADE, related_name='bookings')
    
    # Booking details
    start_date = models.DateField()
    end_date = models.DateField()
    total_hours = models.DecimalField(max_digits=5, decimal_places=2)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Status and notes
    status = models.CharField(max_length=20, choices=BOOKING_STATUS_CHOICES, default='pending')
    special_requests = models.TextField(blank=True)
    guide_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking: {self.tourist.username} -> {self.guide.full_name} ({self.start_date})"
