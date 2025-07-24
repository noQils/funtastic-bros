from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, TourGuideRating

class CustomUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=[('', 'Pilih role')] + User.ROLE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-input w-full rounded-lg px-4 py-2',
            'required': True
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'role')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-input w-full rounded-lg px-4 py-2',
                'placeholder': 'Username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input w-full rounded-lg px-4 py-2',
                'placeholder': 'Email'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-input w-full rounded-lg px-4 py-2',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-input w-full rounded-lg px-4 py-2',
            'placeholder': 'Confirm Password'
        })


class TourGuideRatingForm(forms.ModelForm):
    """Form for rating tour guides"""
    
    class Meta:
        model = TourGuideRating
        fields = ['ramah', 'seru', 'informatif', 'fleksibel', 'easy_going']
        widgets = {
            'ramah': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2'
            }),
            'seru': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2'
            }),
            'informatif': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2'
            }),
            'fleksibel': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2'
            }),
            'easy_going': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2'
            }),
        }
        labels = {
            'ramah': 'Ramah',
            'seru': 'Seru',
            'informatif': 'Informatif',
            'fleksibel': 'Fleksibel',
            'easy_going': 'Easy Going',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.required = False
