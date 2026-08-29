from django.urls import path
from . import views

urlpatterns = [
    path('', views.order_list_create, name='order_list_create'),
    path('<int:order_id>/status/', views.order_status, name='order_status'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
]
