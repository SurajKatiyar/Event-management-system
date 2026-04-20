from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import City, Country, event as Event, registration as Registration


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('This email is already in use.')
        return email

class RegistrationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)
        for field_name in ['name', 'email', 'phone', 'city', 'organization', 'note']:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({'class': 'form-control'})
        self.fields['phone'].required = True
        self.fields['city'].required = True
        self.fields['organization'].required = False
        self.fields['note'].required = False

    def clean_email(self):
        email = self.cleaned_data['email']
        if self.event and Registration.objects.filter(event=self.event, email__iexact=email).exists():
            raise forms.ValidationError('This email is already registered for this event.')
        return email

    class Meta:
        model = Registration
        fields = ['name', 'email', 'phone', 'city', 'organization', 'note']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your phone number'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your city'}),
            'organization': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Organization name (optional)'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Special note (optional)'}),
        }


class EventForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['city'].queryset = City.objects.none()

        if self.data.get('country'):
            self.fields['city'].queryset = City.objects.filter(country_id=self.data.get('country')).order_by('name')
        elif self.instance and self.instance.pk and self.instance.country_id:
            self.fields['city'].queryset = City.objects.filter(country=self.instance.country).order_by('name')
        else:
            self.fields['city'].queryset = City.objects.order_by('name')

    class Meta:
        model = Event
        fields = [
            'title',
            'description',
            'date',
            'time',
            'country',
            'city',
            'venue',
            'capacity',
            'category',
            'image',
            'registration_deadline',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'country': forms.Select(attrs={'class': 'form-select'}),
            'city': forms.Select(attrs={'class': 'form-select'}),
            'venue': forms.TextInput(attrs={'class': 'form-control'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'registration_deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }