from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('guider', 'Guider'),
    ]
    
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='user',
        help_text='Role of the user - either user or guider'
    )
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


