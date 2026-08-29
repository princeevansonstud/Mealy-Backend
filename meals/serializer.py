from rest_framework import serializers
from .models import Meal, Order

class MealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meal
        fields = ['id', 'name', 'description', 'price', 'category', 'is_on_daily_menu', 'created_at']

class OrderSerializer(serializers.ModelSerializer):
    # Maps camelCase keys from React to snake_case Django model fields
    customerName = serializers.CharField(source='customer_name', required=False, allow_blank=True)
    totalAmount = serializers.DecimalField(source='total_amount', max_digits=10, decimal_places=2, required=False)

    class Meta:
        model = Order
        fields = ['id', 'customerName', 'totalAmount', 'status', 'created_at']