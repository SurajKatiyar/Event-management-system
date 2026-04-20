import csv

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.mail import EmailMessage
from django.core.paginator import Paginator
from django.db.models import Count, ExpressionWrapper, F, IntegerField
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import EventForm, RegistrationForm, SignupForm
from .models import Category, City, Country, SavedEvent, event as Event, registration as Registration


def event_list(request):
    search_text = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()
    country_id = request.GET.get('country', '').strip()
    city_id = request.GET.get('city', '').strip()
    sort_by = request.GET.get('sort', 'event_date').strip()

    events = Event.objects.select_related('category', 'country', 'city', 'organizer').annotate(
        registration_count=Count('registration')
    ).annotate(
        seats_left_value=ExpressionWrapper(F('capacity') - F('registration_count'), output_field=IntegerField())
    )

    if search_text:
        events = events.filter(title__icontains=search_text)

    if category_id:
        events = events.filter(category_id=category_id)

    if country_id:
        events = events.filter(country_id=country_id)

    if city_id:
        events = events.filter(city_id=city_id)

    if sort_by == 'newest':
        events = events.order_by('-id')
    elif sort_by == 'popular':
        events = events.order_by('-registration_count', 'date', 'time')
    elif sort_by == 'seats_left':
        events = events.order_by('seats_left_value', 'date', 'time')
    else:
        events = events.order_by('date', 'time')

    paginator = Paginator(events, 6)
    page_obj = paginator.get_page(request.GET.get('page'))

    categories = Category.objects.all().order_by('name')
    countries = Country.objects.all().order_by('name')
    cities = City.objects.filter(country_id=country_id).order_by('name') if country_id else City.objects.none()

    saved_event_ids = set()
    if request.user.is_authenticated:
        saved_event_ids = set(SavedEvent.objects.filter(user=request.user).values_list('event_id', flat=True))

    return render(
        request,
        'eventlist.html',
        {
            'events': page_obj,
            'page_obj': page_obj,
            'search_text': search_text,
            'categories': categories,
            'countries': countries,
            'cities': cities,
            'selected_category': category_id,
            'selected_country': country_id,
            'selected_city': city_id,
            'selected_sort': sort_by,
            'saved_event_ids': saved_event_ids,
        },
    )


def event_detail(request, event_id):
    event = get_object_or_404(Event.objects.select_related('category', 'country', 'city', 'organizer'), id=event_id)
    registration_count = Registration.objects.filter(event=event).count()
    seats_left = max(event.capacity - registration_count, 0)
    seats_percentage = int((registration_count / event.capacity) * 100) if event.capacity else 0
    related_events = Event.objects.select_related('city', 'category').filter(category=event.category).exclude(id=event.id).order_by('date', 'time')[:3]
    is_bookmarked = False
    if request.user.is_authenticated:
        is_bookmarked = SavedEvent.objects.filter(user=request.user, event=event).exists()
    share_url = request.build_absolute_uri()

    return render(
        request,
        'event_detail.html',
        {
            'event': event,
            'registration_count': registration_count,
            'seats_left': seats_left,
            'seats_percentage': seats_percentage,
            'related_events': related_events,
            'is_bookmarked': is_bookmarked,
            'share_url': share_url,
        },
    )


@login_required
def register_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if event.registration_deadline:
        today = timezone.localdate()
        if event.registration_deadline < today:
            messages.error(request, 'Registration deadline has passed for this event.')
            return redirect('event_detail', event_id=event.id)

    if Registration.objects.filter(event=event, user=request.user).exists():
        existing_registration = Registration.objects.filter(event=event, user=request.user).first()
        messages.info(request, 'You are already registered for this event.')
        return redirect('ticket', ticket_id=existing_registration.ticket_id)

    total_registrations = Registration.objects.filter(event=event).count()
    if event.capacity and total_registrations >= event.capacity:
        messages.error(request, 'This event is full.')
        return redirect('event_detail', event_id=event.id)

    return redirect('complete_registration', event_id=event_id)


@login_required
def complete_registration(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if event.registration_deadline and event.registration_deadline < timezone.localdate():
        messages.error(request, 'Registration deadline has passed for this event.')
        return redirect('event_detail', event_id=event.id)

    if Registration.objects.filter(event=event, user=request.user).exists():
        existing_registration = Registration.objects.filter(event=event, user=request.user).first()
        messages.info(request, 'You already have a ticket for this event.')
        return redirect('ticket', ticket_id=existing_registration.ticket_id)

    total_registrations = Registration.objects.filter(event=event).count()
    if event.capacity and total_registrations >= event.capacity:
        messages.error(request, 'This event has reached full capacity.')
        return redirect('event_detail', event_id=event.id)

    if request.method == 'POST':
        form = RegistrationForm(request.POST, event=event)
        if form.is_valid():
            reg = form.save(commit=False)
            reg.event = event
            reg.user = request.user
            reg.save()

            email_subject = 'Event Ticket'
            email_body = (
                'Thank you for registering.\n\n'
                f'Event: {event.title}\n'
                f'Ticket ID: {reg.ticket_id}\n'
            )
            email = EmailMessage(
                email_subject,
                email_body,
                to=[reg.email],
            )
            if reg.qr_code:
                with open(reg.qr_code.path, 'rb') as qr_file:
                    email.attach(reg.qr_code.name.split('/')[-1], qr_file.read(), 'image/png')
            email.send(fail_silently=True)

            messages.success(request, 'Registration completed successfully.')
            return redirect('ticket', ticket_id=reg.ticket_id)

    else:
        form = RegistrationForm(event=event)

    return render(request, 'complete_registration.html', {'form': form, 'event': event})


def ticket_view(request, ticket_id):
    registration = get_object_or_404(Registration.objects.select_related('event', 'user', 'event__organizer'), ticket_id=ticket_id)
    can_check_in = request.user.is_authenticated and registration.event.organizer_id == request.user.id
    return render(request, 'ticket.html', {'registration': registration, 'can_check_in': can_check_in})


@login_required
def download_ticket(request, ticket_id):
    registration = get_object_or_404(Registration.objects.select_related('event'), ticket_id=ticket_id)
    if registration.user_id != request.user.id and registration.event.organizer_id != request.user.id:
        messages.error(request, 'You are not allowed to download this ticket.')
        return redirect('event_list')

    if not registration.qr_code:
        messages.error(request, 'QR ticket not found.')
        return redirect('ticket', ticket_id=registration.ticket_id)

    with open(registration.qr_code.path, 'rb') as qr_file:
        response = HttpResponse(qr_file.read(), content_type='image/png')
        response['Content-Disposition'] = f'attachment; filename="ticket_{registration.ticket_id}.png"'
        return response


@login_required
def dashboard(request):
    my_tickets = Registration.objects.select_related('event').filter(user=request.user).order_by('-id')
    my_created_events = Event.objects.filter(organizer=request.user).order_by('date', 'time')
    saved_events_count = SavedEvent.objects.filter(user=request.user).count()
    return render(
        request,
        'dashboard.html',
        {
            'my_tickets': my_tickets,
            'my_created_events': my_created_events,
            'saved_events_count': saved_events_count,
        },
    )


@login_required
def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            new_event = form.save(commit=False)
            new_event.organizer = request.user
            new_event.save()
            messages.success(request, 'Event created successfully.')
            return redirect('my_events')
    else:
        form = EventForm()

    return render(request, 'create_event.html', {'form': form})


@login_required
def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id, organizer=request.user)
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event updated successfully.')
            return redirect('my_events')
    else:
        form = EventForm(instance=event)

    return render(request, 'edit_event.html', {'form': form, 'event': event})


@login_required
def my_tickets(request):
    registrations = Registration.objects.select_related('event').filter(user=request.user).order_by('-id')
    return render(request, 'my_tickets.html', {'registrations': registrations})


@login_required
def my_events(request):
    events = Event.objects.filter(organizer=request.user).annotate(registration_count=Count('registration')).order_by('date', 'time')
    return render(request, 'my_events.html', {'events': events})


@login_required
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id, organizer=request.user)
    if request.method == 'POST':
        event.delete()
        messages.success(request, 'Event deleted successfully.')
        return redirect('my_events')

    return render(request, 'delete_event_confirm.html', {'event': event})


@login_required
def event_attendees(request, event_id):
    event = get_object_or_404(Event, id=event_id, organizer=request.user)
    attendees = Registration.objects.filter(event=event).order_by('name')
    return render(request, 'event_attendees.html', {'event': event, 'attendees': attendees})


@login_required
def export_attendees_csv(request, event_id):
    event = get_object_or_404(Event, id=event_id, organizer=request.user)
    attendees = Registration.objects.filter(event=event).order_by('name')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="attendees_{event.id}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Email', 'Phone', 'City', 'Organization', 'Ticket ID', 'Checked In'])

    for attendee in attendees:
        writer.writerow([
            attendee.name,
            attendee.email,
            attendee.phone,
            attendee.city,
            attendee.organization,
            attendee.ticket_id,
            'Yes' if attendee.is_checked_in else 'No',
        ])

    return response


@login_required
def check_in_attendee(request, ticket_id):
    registration = get_object_or_404(Registration.objects.select_related('event'), ticket_id=ticket_id)
    if registration.event.organizer_id != request.user.id:
        messages.error(request, 'Only organizer can check in attendees.')
        return redirect('event_list')

    registration.is_checked_in = True
    registration.save(update_fields=['is_checked_in'])
    messages.success(request, f'{registration.name} marked as present.')
    return redirect('event_attendees', event_id=registration.event.id)


def organizer_profile(request, organizer_id):
    from django.contrib.auth.models import User

    organizer = get_object_or_404(User, id=organizer_id)
    events = Event.objects.filter(organizer=organizer).annotate(registration_count=Count('registration')).order_by('date', 'time')
    return render(request, 'organizer_profile.html', {'organizer': organizer, 'events': events})


@login_required
def toggle_bookmark(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    saved_item = SavedEvent.objects.filter(user=request.user, event=event).first()
    if saved_item:
        saved_item.delete()
        messages.success(request, 'Event removed from saved list.')
    else:
        SavedEvent.objects.create(user=request.user, event=event)
        messages.success(request, 'Event saved successfully.')

    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('event_detail', event_id=event.id)


@login_required
def saved_events(request):
    saved_items = SavedEvent.objects.select_related('event', 'event__city', 'event__category').filter(user=request.user).order_by('-created_at')
    return render(request, 'saved_events.html', {'saved_items': saved_items})


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('event_list')

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully.')
            return redirect('event_list')
    else:
        form = SignupForm()

    return render(request, 'signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('event_list')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Logged in successfully.')
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('event_list')
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('event_list')


def registered_users(request):
    registrations = Registration.objects.select_related('event').order_by('event__date', 'name')
    return render(request, 'users.html', {'registrations': registrations})