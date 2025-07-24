from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

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
