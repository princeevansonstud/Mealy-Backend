from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MealViewSet,
    OrderViewSet,
    MealOptionListCreateView,
    MealOptionDetailView,
    DailyMenuListCreateView,
    DailyMenuTodayView,
    DailyMenuItemCreateView,
)

router = DefaultRouter()
router.register(r'meals-viewset', MealViewSet, basename='meal')
router.register(r'orders-viewset', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
    path("options/", MealOptionListCreateView.as_view(), name="meal-options"),
    path("options/<int:pk>/", MealOptionDetailView.as_view(),
         name="meal-option-detail"),
    path("<int:pk>/", MealOptionDetailView.as_view(), name="meal-detail-direct"),
    path("daily-menu/", DailyMenuListCreateView.as_view(), name="daily-menu"),
    path("daily-menu/today/", DailyMenuTodayView.as_view(), name="daily-menu-today"),
    path("daily-menu-items/", DailyMenuItemCreateView.as_view(),
         name="daily-menu-items"),
]
