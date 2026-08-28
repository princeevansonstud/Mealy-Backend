from django.urls import path

from .views import (
    DailyMenuItemCreateView,
    DailyMenuListCreateView,
    DailyMenuTodayView,
    MealOptionListCreateView,
)


urlpatterns = [
    path("options/", MealOptionListCreateView.as_view(), name="meal-options"),
    path("daily-menu/", DailyMenuListCreateView.as_view(), name="daily-menu"),
    path("daily-menu/today/", DailyMenuTodayView.as_view(), name="daily-menu-today"),
    path("daily-menu-items/", DailyMenuItemCreateView.as_view(), name="daily-menu-items"),
]