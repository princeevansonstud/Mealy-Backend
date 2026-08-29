from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from meals.models import DailyMenuItem, MealOption
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderCreateSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def order_list_create(request):
    session = request.db  # Request-scoped SQLAlchemy session attached by middleware
    authenticated_user_id = request.user.id

    if request.method == 'GET':
        # Restrict order history strictly to the authenticated user
        orders = (
            session.query(Order)
            .filter(Order.user_id == authenticated_user_id)
            .order_by(Order.created_at.desc())
            .all()
        )
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = OrderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        items_data = serializer.validated_data['items']

        calculated_total = 0.0
        validated_order_items = []

        # Validate existence & calculate true server-side pricing
        for item in items_data:
            daily_item_id = item['daily_menu_item_id']
            quantity = item['quantity']

            daily_item = session.get(DailyMenuItem, daily_item_id)
            if not daily_item:
                return Response(
                    {"error": f"Daily menu item {daily_item_id} does not exist."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            meal = session.get(MealOption, daily_item.meal_option_id)
            if not meal:
                return Response(
                    {"error": f"Meal option for item {daily_item_id} not found."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            item_price = float(meal.price)
            calculated_total += item_price * quantity

            validated_order_items.append({
                "meal_title": meal.title,
                "quantity": quantity,
                "price": item_price
            })

        # Create Order record with server-validated data
        new_order = Order(
            user_id=authenticated_user_id,
            total_amount=calculated_total,
            status="Pending"
        )
        session.add(new_order)
        session.flush()  # Generates new_order.id

        # Attach line items
        for order_item_data in validated_order_items:
            order_item = OrderItem(
                order_id=new_order.id,
                meal_title=order_item_data["meal_title"],
                quantity=order_item_data["quantity"],
                price=order_item_data["price"]
            )
            session.add(order_item)

        session.commit()
        session.refresh(new_order)

        return Response(
            OrderSerializer(new_order).data,
            status=status.HTTP_201_CREATED
        )
