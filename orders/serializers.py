from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemInputSerializer(serializers.Serializer):
    daily_menu_item_id = serializers.IntegerField(
        required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1)
    price = serializers.FloatField(required=False)
    unit_price = serializers.FloatField(required=False)


class OrderCreateSerializer(serializers.Serializer):
    items = OrderItemInputSerializer(many=True)


class OrderItemDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    meal_title = serializers.CharField(read_only=True)
    quantity = serializers.IntegerField()
    unit_price = serializers.FloatField(source='price', default=0.0)


class OrderSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    total_price = serializers.FloatField(source='total_amount', read_only=True)
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True, required=False)
    items = serializers.SerializerMethodField()

    def get_items(self, order):
        session = self.context["request"].db
        items = session.query(OrderItem).filter(
            OrderItem.order_id == order.id).all()
        return OrderItemDetailSerializer(items, many=True).data
