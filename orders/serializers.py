from rest_framework import serializers
from .models import Order, OrderItem
from meals.models import DailyMenuItem, MealOption


class OrderItemInputSerializer(serializers.Serializer):
    daily_menu_item_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.Serializer):
    items = OrderItemInputSerializer(many=True)


class OrderItemDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    daily_menu_item_id = serializers.IntegerField()
    quantity = serializers.IntegerField()
    unit_price = serializers.FloatField()
    title = serializers.SerializerMethodField()

    def get_title(self, obj):
        session = self.context["request"].db
        daily_item = session.get(DailyMenuItem, obj.daily_menu_item_id)
        if daily_item:
            meal = session.get(MealOption, daily_item.meal_option_id)
            return meal.title if meal else None
        return None


class OrderSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    total_price = serializers.FloatField(read_only=True)
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True, required=False)
    items = serializers.SerializerMethodField()

    def get_items(self, order):
        session = self.context["request"].db
        items = session.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        return OrderItemDetailSerializer(items, many=True, context=self.context).data