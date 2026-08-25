# meals/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.meal_list_create, name='meal-list-create'),
]
