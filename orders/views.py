from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from config.db import get_db
from .models import Order, OrderItem


@api_view(['GET', 'POST'])
def order_list_create(request):
    db = get_db()

    if request.method == 'GET':
        user_id = request.query_params.get('user_id')

        query = db.query(Order)
        if user_id:
            query = query.filter(Order.user_id == user_id)

        orders = query.order_by(Order.created_at.desc()).all()

        data = []
        for order in orders:
            data.append({
                "id": order.id,
                "user_id": order.user_id,
                "total_amount": order.total_amount,
                "status": order.status,
                "created_at": order.created_at.isoformat(),
                "items": [
                    {
                        "id": item.id,
                        "meal_title": item.meal_title,
                        "quantity": item.quantity,
                        "price": item.price
                    } for item in order.items
                ]
            })
        return Response(data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        user_id = request.data.get('user_id')
        items_data = request.data.get('items', [])
        total_amount = request.data.get('total_amount')

        if not user_id or not items_data:
            return Response({"error": "user_id and items are required"}, status=status.HTTP_400_BAD_REQUEST)

        new_order = Order(
            user_id=user_id,
            total_amount=total_amount,
            status="Pending"
        )
        db.add(new_order)
        db.flush()

        for item in items_data:
            order_item = OrderItem(
                order_id=new_order.id,
                meal_title=item.get('meal_title'),
                quantity=item.get('quantity'),
                price=item.get('price')
            )
            db.add(order_item)

        db.commit()
        db.refresh(new_order)

        return Response({"message": "Order created successfully", "order_id": new_order.id}, status=status.HTTP_201_CREATED)
