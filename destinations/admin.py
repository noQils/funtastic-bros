from django.contrib import admin
from .models import City, DestinationCategory, Destination, DestinationImage, DestinationReview

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'province', 'country', 'is_active', 'created_at']
    list_filter = ['province', 'country', 'is_active']
    search_fields = ['name', 'province']

@admin.register(DestinationCategory)
class DestinationCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon']
    search_fields = ['name']

@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'category', 'rating', 'popularity_score', 'average_cost', 'is_active']
    list_filter = ['city', 'category', 'is_active', 'is_featured']
    search_fields = ['name', 'description']
    ordering = ['-popularity_score', '-rating']

@admin.register(DestinationImage)
class DestinationImageAdmin(admin.ModelAdmin):
    list_display = ['destination', 'caption', 'is_primary', 'uploaded_at']
    list_filter = ['is_primary', 'uploaded_at']

@admin.register(DestinationReview)
class DestinationReviewAdmin(admin.ModelAdmin):
    list_display = ['destination', 'reviewer_name', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['reviewer_name', 'destination__name']
