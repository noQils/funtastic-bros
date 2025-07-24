from django.contrib import admin
from .models import TravelInterest, Itinerary, ItineraryDay, ItineraryActivity, SavedItinerary, ItineraryGuideRequest

@admin.register(TravelInterest)
class TravelInterestAdmin(admin.ModelAdmin):
    list_display = ['name', 'keywords']
    search_fields = ['name', 'keywords']

class ItineraryDayInline(admin.TabularInline):
    model = ItineraryDay
    extra = 0

class ItineraryActivityInline(admin.TabularInline):
    model = ItineraryActivity
    extra = 0

@admin.register(Itinerary)
class ItineraryAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'city', 'duration_days', 'budget_range', 'estimated_total_cost', 'is_favorite', 'created_at']
    list_filter = ['city', 'budget_range', 'is_favorite', 'is_public', 'created_at']
    search_fields = ['title', 'user__username']
    filter_horizontal = ['interests']
    inlines = [ItineraryDayInline]

@admin.register(ItineraryDay)
class ItineraryDayAdmin(admin.ModelAdmin):
    list_display = ['itinerary', 'day_number', 'title', 'estimated_daily_cost']
    list_filter = ['day_number']
    search_fields = ['itinerary__title', 'title']
    inlines = [ItineraryActivityInline]

@admin.register(ItineraryActivity)
class ItineraryActivityAdmin(admin.ModelAdmin):
    list_display = ['day', 'title', 'activity_type', 'start_time', 'end_time', 'estimated_cost']
    list_filter = ['activity_type', 'day__day_number']
    search_fields = ['title', 'day__itinerary__title']

@admin.register(SavedItinerary)
class SavedItineraryAdmin(admin.ModelAdmin):
    list_display = ['user', 'itinerary', 'saved_at']
    list_filter = ['saved_at']
    search_fields = ['user__username', 'itinerary__title']

@admin.register(ItineraryGuideRequest)
class ItineraryGuideRequestAdmin(admin.ModelAdmin):
    list_display = ['itinerary', 'status', 'max_budget_per_day', 'preferred_guide', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['itinerary__title']
    filter_horizontal = ['matched_guides']
