from django.contrib import admin

# Register your models here.
from .models import Category, City, Country, SavedEvent, event, registration


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	list_display = ('name',)
	search_fields = ('name',)


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
	list_display = ('name',)
	search_fields = ('name',)


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
	list_display = ('name', 'country')
	search_fields = ('name', 'country__name')
	list_filter = ('country',)

@admin.register(event)
class EventAdmin(admin.ModelAdmin):
	list_display = ('title', 'organizer', 'date', 'country', 'city', 'venue', 'capacity', 'category')
	search_fields = ('title', 'venue', 'city__name', 'country__name', 'category__name', 'organizer__username')
	list_filter = ('date', 'country', 'category')


@admin.register(registration)
class RegistrationAdmin(admin.ModelAdmin):
	list_display = ('name', 'email', 'phone', 'ticket_id', 'event', 'user', 'is_checked_in')
	search_fields = ('name', 'email', 'ticket_id', 'phone', 'event__title', 'user__username')
	list_filter = ('event', 'is_checked_in')


@admin.register(SavedEvent)
class SavedEventAdmin(admin.ModelAdmin):
	list_display = ('user', 'event', 'created_at')
	search_fields = ('user__username', 'event__title')
	list_filter = ('created_at',)