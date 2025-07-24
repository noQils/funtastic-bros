from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('guider', 'Tour Guide'),
    ]
    
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='user',
        help_text='Role of the user - either user or guider'
    )
    
    # Rating fields for tour guides
    ramah_count = models.IntegerField(default=0, help_text='Number of "ramah" ratings')
    seru_count = models.IntegerField(default=0, help_text='Number of "seru" ratings')
    informatif_count = models.IntegerField(default=0, help_text='Number of "informatif" ratings')
    fleksibel_count = models.IntegerField(default=0, help_text='Number of "fleksibel" ratings')
    easy_going_count = models.IntegerField(default=0, help_text='Number of "easy going" ratings')
    total_ratings = models.IntegerField(default=0, help_text='Total number of people who rated this guide')
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def get_rating_percentage(self, rating_type):
        """Get percentage for a specific rating type"""
        if self.total_ratings == 0:
            return 0
        rating_count = getattr(self, f"{rating_type}_count", 0)
        return round((rating_count / self.total_ratings) * 100, 1)
    
    def get_all_ratings(self):
        """Get all ratings as a dictionary"""
        return {
            'ramah': self.ramah_count,
            'seru': self.seru_count,
            'informatif': self.informatif_count,
            'fleksibel': self.fleksibel_count,
            'easy_going': self.easy_going_count,
        }
    
    def get_rating_percentages(self):
        """Get all rating percentages"""
        return {
            'ramah': self.get_rating_percentage('ramah'),
            'seru': self.get_rating_percentage('seru'),
            'informatif': self.get_rating_percentage('informatif'),
            'fleksibel': self.get_rating_percentage('fleksibel'),
            'easy_going': self.get_rating_percentage('easy_going'),
        }


class TourGuideRating(models.Model):
    """Model to track individual ratings to prevent duplicate ratings"""
    rater = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_ratings')
    tour_guide = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_ratings')
    
    # Rating categories
    ramah = models.BooleanField(default=False)
    seru = models.BooleanField(default=False)
    informatif = models.BooleanField(default=False)
    fleksibel = models.BooleanField(default=False)
    easy_going = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('rater', 'tour_guide')
        verbose_name = 'Tour Guide Rating'
        verbose_name_plural = 'Tour Guide Ratings'
    
    def __str__(self):
        return f"{self.rater.username} rated {self.tour_guide.username}"
    
    def get_selected_ratings(self):
        """Get list of selected rating categories"""
        ratings = []
        if self.ramah:
            ratings.append('ramah')
        if self.seru:
            ratings.append('seru')
        if self.informatif:
            ratings.append('informatif')
        if self.fleksibel:
            ratings.append('fleksibel')
        if self.easy_going:
            ratings.append('easy_going')
        return ratings


