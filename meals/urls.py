from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MealViewSet, OrderViewSet
from .views import (
    MealOptionListCreateView,
    DailyMenuListCreateView,
    DailyMenuTodayView,
    DailyMenuItemCreateView,
)

router = DefaultRouter()
router.register(r'meals', MealViewSet, basename='meal')
router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),

]

urlpatterns = [
    path("options/", MealOptionListCreateView.as_view(), name="meal-options"),
    path("daily-menu/", DailyMenuListCreateView.as_view(), name="daily-menu"),
    path("daily-menu/today/", DailyMenuTodayView.as_view(), name="daily-menu-today"),
    path("daily-menu-items/", DailyMenuItemCreateView.as_view(), name="daily-menu-items"),
]