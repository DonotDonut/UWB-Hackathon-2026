from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('add-person/', views.add_person, name='add_person'),
    path('schedules/', views.schedules, name='schedules'),
    path('edit-shift/', views.edit_shift, name='edit_shift'),
    path("create-suggested-schedule/", views.create_suggested_schedule, name="create_suggested_schedule")
]