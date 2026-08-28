from django.urls import path
from . import views

urlpatterns = [
    path("", views.order_list, name="order-list"),
    path("<int:order_id>/", views.order_detail, name="order-detail"),
    path(
        "<int:order_id>/status/",
        views.update_order_status,
        name="update-order-status"
    ),
    path("earnings/", views.earnings, name="earnings"),
]