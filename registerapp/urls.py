from django.urls import path
from . import views

urlpatterns = [
    path('', views.event_list, name='event_list'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('saved-events/', views.saved_events, name='saved_events'),
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),
    path('event/<int:event_id>/bookmark/', views.toggle_bookmark, name='toggle_bookmark'),
    path('organizer/<int:organizer_id>/', views.organizer_profile, name='organizer_profile'),
    path('events/<int:event_id>/', views.event_detail, name='event_detail_legacy'),
    path('create-event/', views.create_event, name='create_event'),
    path('edit-event/<int:event_id>/', views.edit_event, name='edit_event'),
    path('delete-event/<int:event_id>/', views.delete_event, name='delete_event'),
    path('register/<int:event_id>/', views.register_event, name='register_event'),
    path('complete-registration/<int:event_id>/', views.complete_registration, name='complete_registration'),
    path('my-tickets/', views.my_tickets, name='my_tickets'),
    path('my-events/', views.my_events, name='my_events'),
    path('my-events/<int:event_id>/attendees/', views.event_attendees, name='event_attendees'),
    path('my-events/<int:event_id>/attendees/export/', views.export_attendees_csv, name='export_attendees_csv'),
    path('check-in/<str:ticket_id>/', views.check_in_attendee, name='check_in_attendee'),
    path('ticket/<str:ticket_id>/', views.ticket_view, name='ticket'),
    path('ticket/<str:ticket_id>/download/', views.download_ticket, name='download_ticket'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('users/', views.registered_users, name='registered_users'),
]