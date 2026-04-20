from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import EventForm, RegistrationForm
from .models import Category, City, Country, event as Event


class SecurityAccessTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='user1', password='pass12345')
		self.staff = User.objects.create_user(username='staff1', password='pass12345', is_staff=True)

	def test_registered_users_requires_login(self):
		response = self.client.get(reverse('registered_users'))
		self.assertEqual(response.status_code, 302)
		self.assertIn(reverse('login'), response.url)

	def test_registered_users_requires_staff(self):
		self.client.login(username='user1', password='pass12345')
		response = self.client.get(reverse('registered_users'), follow=True)
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'eventlist.html')

	def test_registered_users_allows_staff(self):
		self.client.login(username='staff1', password='pass12345')
		response = self.client.get(reverse('registered_users'))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'users.html')


class PostOnlyViewTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='user2', password='pass12345')
		self.country = Country.objects.create(name='India')
		self.city = City.objects.create(name='Delhi', country=self.country)
		self.category = Category.objects.create(name='Tech')
		self.event = Event.objects.create(
			organizer=self.user,
			title='Django Meetup',
			description='A meetup',
			date=timezone.localdate() + timedelta(days=10),
			country=self.country,
			city=self.city,
			venue='Hall A',
			capacity=100,
			category=self.category,
		)
		self.client.login(username='user2', password='pass12345')

	def test_toggle_bookmark_get_is_not_allowed(self):
		response = self.client.get(reverse('toggle_bookmark', args=[self.event.id]))
		self.assertEqual(response.status_code, 405)


class FormValidationTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='user3', password='pass12345')
		self.country = Country.objects.create(name='Canada')
		self.city = City.objects.create(name='Toronto', country=self.country)
		self.other_country = Country.objects.create(name='India')
		self.other_city = City.objects.create(name='Mumbai', country=self.other_country)
		self.category = Category.objects.create(name='Workshop')
		self.event = Event.objects.create(
			organizer=self.user,
			title='Python Workshop',
			description='Hands-on workshop',
			date=timezone.localdate() + timedelta(days=15),
			country=self.country,
			city=self.city,
			venue='Center',
			capacity=50,
			category=self.category,
		)

	def test_registration_form_rejects_invalid_phone(self):
		form = RegistrationForm(
			data={
				'name': 'Test User',
				'email': 'test@example.com',
				'phone': '1234',
				'city': 'Toronto',
				'organization': '',
				'note': '',
			},
			event=self.event,
		)
		self.assertFalse(form.is_valid())
		self.assertIn('phone', form.errors)

	def test_event_form_rejects_mismatched_city_country(self):
		form = EventForm(
			data={
				'title': 'Bad City Mapping',
				'description': 'desc',
				'date': (timezone.localdate() + timedelta(days=5)).isoformat(),
				'time': '10:00',
				'country': self.country.id,
				'city': self.other_city.id,
				'venue': 'Venue',
				'capacity': 10,
				'category': self.category.id,
				'registration_deadline': (timezone.localdate() + timedelta(days=4)).isoformat(),
			}
		)
		self.assertFalse(form.is_valid())
		self.assertIn('city', form.errors)

	def test_event_form_rejects_deadline_after_event_date(self):
		form = EventForm(
			data={
				'title': 'Late Deadline Event',
				'description': 'desc',
				'date': (timezone.localdate() + timedelta(days=5)).isoformat(),
				'time': '10:00',
				'country': self.country.id,
				'city': self.city.id,
				'venue': 'Venue',
				'capacity': 10,
				'category': self.category.id,
				'registration_deadline': (timezone.localdate() + timedelta(days=7)).isoformat(),
			}
		)
		self.assertFalse(form.is_valid())
		self.assertIn('registration_deadline', form.errors)
