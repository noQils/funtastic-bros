from django.contrib import admin
from .models import Language, PersonalityTrait, TourGuide, GuideAvailability, GuideReview, Booking

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
    search_fields = ['name', 'code']

@admin.register(PersonalityTrait)
class PersonalityTraitAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(TourGuide)
class TourGuideAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'years_of_experience', 'average_rating', 'total_reviews', 'hourly_rate', 'is_available', 'is_verified']
    list_filter = ['is_available', 'is_verified', 'years_of_experience', 'cities']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    filter_horizontal = ['specialties', 'languages', 'personality_traits', 'cities']

@admin.register(GuideAvailability)
class GuideAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['guide', 'date', 'is_available', 'notes']
    list_filter = ['is_available', 'date']
    search_fields = ['guide__user__username']

@admin.register(GuideReview)
class GuideReviewAdmin(admin.ModelAdmin):
    list_display = ['guide', 'reviewer', 'rating', 'tour_date', 'is_verified', 'created_at']
    list_filter = ['rating', 'is_verified', 'tour_date', 'created_at']
    search_fields = ['guide__user__username', 'reviewer__username']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['tourist', 'guide', 'start_date', 'end_date', 'total_cost', 'status', 'created_at']
    list_filter = ['status', 'start_date', 'created_at']
    search_fields = ['tourist__username', 'guide__user__username']
