from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Category, City, Country, event as Event, registration as Registration


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
        email = self.cleaned_data['email'].strip().lower()
        if self.event and Registration.objects.filter(event=self.event, email__iexact=email).exists():
            raise forms.ValidationError('This email is already registered for this event.')
        return email

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        digits_only = ''.join(ch for ch in phone if ch.isdigit())
        if len(digits_only) < 10 or len(digits_only) > 15:
            raise forms.ValidationError('Please enter a valid phone number (10 to 15 digits).')
        return phone

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
    new_category = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Type a new category (optional)',
            }
        ),
        help_text='If provided, this will be created and used for this event.',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['city'].queryset = City.objects.none()
        self.fields['category'].queryset = Category.objects.order_by('name')

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

    def clean_new_category(self):
        return self.cleaned_data.get('new_category', '').strip()

    def clean_capacity(self):
        capacity = self.cleaned_data.get('capacity')
        if capacity is not None and capacity < 1:
            raise forms.ValidationError('Capacity must be at least 1.')
        return capacity

    def clean(self):
        cleaned_data = super().clean()
        event_date = cleaned_data.get('date')
        registration_deadline = cleaned_data.get('registration_deadline')
        country = cleaned_data.get('country')
        city = cleaned_data.get('city')
        new_category = cleaned_data.get('new_category')

        if event_date and event_date < timezone.localdate():
            self.add_error('date', 'Event date cannot be in the past.')

        if event_date and registration_deadline and registration_deadline > event_date:
            self.add_error('registration_deadline', 'Registration deadline cannot be after event date.')

        if city and country and city.country_id != country.id:
            self.add_error('city', 'Selected city does not belong to selected country.')

        if new_category and len(new_category) < 2:
            self.add_error('new_category', 'New category must be at least 2 characters long.')

        return cleaned_data

    def save(self, commit=True):
        event_instance = super().save(commit=False)
        new_category = self.cleaned_data.get('new_category')

        if new_category:
            category = Category.objects.filter(name__iexact=new_category).first()
            if not category:
                category = Category.objects.create(name=new_category)
            event_instance.category = category

        if commit:
            event_instance.save()
            self.save_m2m()

        return event_instance