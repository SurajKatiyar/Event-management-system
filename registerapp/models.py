import secrets
from io import BytesIO

import qrcode
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db import models
from django.utils.text import slugify
from django.utils import timezone

# Create your models here.


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)




















    def __str__(self):
        return self.name


class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class City(models.Model):
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='cities')

    class Meta:
        unique_together = ('name', 'country')

    def __str__(self):
        return f"{self.name}, {self.country.name}"


class event(models.Model):
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_events', blank=True, null=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, blank=True, null=True, related_name='events')
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, blank=True, null=True, related_name='events')
    city = models.ForeignKey(City, on_delete=models.SET_NULL, blank=True, null=True, related_name='events')
    venue = models.CharField(max_length=200, blank=True, default='')
    time = models.TimeField(blank=True, null=True)
    capacity = models.PositiveIntegerField(default=100)
    image = models.ImageField(upload_to='event_images/', blank=True, null=True)
    registration_deadline = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.title

    def seats_filled(self):
        return getattr(self, 'registration_count', self.registration_set.count())

    def seats_left(self):
        return max(self.capacity - self.seats_filled(), 0)

    def status_label(self):
        today = timezone.localdate()
        if self.date < today:
            return 'Completed'
        if self.registration_deadline and self.registration_deadline < today:
            return 'Registration Closed'
        if self.capacity and self.seats_filled() >= self.capacity:
            return 'Sold Out'
        return 'Upcoming'

    def status_badge_class(self):
        status = self.status_label()
        if status == 'Upcoming':
            return 'text-bg-success'
        if status == 'Sold Out':
            return 'text-bg-danger'
        if status == 'Registration Closed':
            return 'text-bg-warning'
        return 'text-bg-secondary'
    

class registration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registrations', blank=True, null=True)
    event = models.ForeignKey(event, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    organization = models.CharField(max_length=150, blank=True, default='')
    note = models.TextField(blank=True, default='')
    ticket_id = models.CharField(max_length=32, unique=True, blank=True, null=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    is_checked_in = models.BooleanField(default=False)
    attended = models.BooleanField(default=False)
    attendance_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['event', 'email'], name='unique_event_email_registration')
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.ticket_id:
            self.ticket_id = self.generate_unique_ticket_id()

        if self.attended and not self.is_checked_in:
            self.is_checked_in = True
        elif self.is_checked_in and not self.attended:
            self.attended = True

        super().save(*args, **kwargs)

        if not self.qr_code:
            qr_img = self.generate_qr_image()

            buffer = BytesIO()
            qr_img.save(buffer, format='PNG')

            event_slug = slugify(self.event.title)
            file_name = f"ticket_{event_slug}_{self.id}.png"
            self.qr_code.save(file_name, ContentFile(buffer.getvalue()), save=False)

            super().save(update_fields=['qr_code'])

    def generate_qr_payload(self):
        return f"registration:{self.id}"

    def generate_qr_image(self):
        return qrcode.make(self.generate_qr_payload())

    def generate_unique_ticket_id(self):
        ticket_id = secrets.token_urlsafe(8).replace('-', '').replace('_', '').upper()
        while registration.objects.filter(ticket_id=ticket_id).exists():
            ticket_id = secrets.token_urlsafe(8).replace('-', '').replace('_', '').upper()
        return ticket_id


class SavedEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_events')
    event = models.ForeignKey(event, on_delete=models.CASCADE, related_name='saved_by_users')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'event'], name='unique_user_saved_event')
        ]

    def __str__(self):
        return f"{self.user.username} - {self.event.title}"