from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class City(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    country = models.CharField(max_length=100, default='Indonesia')
    province = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Cities"

    def __str__(self):
        return f"{self.name}, {self.province}"


class DestinationCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, help_text="FontAwesome icon class")

    class Meta:
        verbose_name_plural = "Destination Categories"

    def __str__(self):
        return self.name


class Destination(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='destinations')
    category = models.ForeignKey(DestinationCategory, on_delete=models.CASCADE, related_name='destinations')
    
    # Location details
    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Pricing and duration
    average_cost = models.DecimalField(max_digits=10, decimal_places=2, help_text="Average cost in IDR")
    estimated_duration_hours = models.DecimalField(max_digits=4, decimal_places=2, help_text="Estimated visit duration in hours")
    
    # Ratings and popularity
    rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        default=0
    )
    popularity_score = models.IntegerField(default=0, help_text="Higher score = more popular")
    
    # Operational details
    opening_hours = models.CharField(max_length=200, help_text="e.g., '08:00-17:00' or '24 hours'")
    best_time_to_visit = models.CharField(max_length=100, help_text="e.g., 'Morning', 'Evening', 'Anytime'")
    
    # Media and additional info
    image_url = models.URLField(blank=True, help_text="Main image URL")
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-popularity_score', '-rating']

    def __str__(self):
        return f"{self.name} - {self.city.name}"

    @property
    def coordinates(self):
        if self.latitude and self.longitude:
            return f"{self.latitude},{self.longitude}"
        return None


class DestinationImage(models.Model):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='images')
    image_url = models.URLField()
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.destination.name}"


class DestinationReview(models.Model):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='reviews')
    reviewer_name = models.CharField(max_length=100)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reviewer_name} - {self.destination.name} ({self.rating}/5)"
