from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderCreateSerializer
from .services import initiate_stk_push


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def order_list_create(request):
    session = request.db
    authenticated_user_id = getattr(request.user, 'id', request.user)

    if request.method == 'GET':
        orders = (
            session.query(Order)
            .filter(Order.user_id == authenticated_user_id)
            .order_by(Order.created_at.desc())
            .all()
        )
        return Response(OrderSerializer(orders, many=True, context={"request": request}).data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = OrderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        items_data = request.data.get('items', [])
        validated_items = serializer.validated_data['items']
        phone_number = request.data.get('phone_number')

        raw_total = request.data.get(
            'total_amount') or request.data.get('total_price')

        calculated_total = 0.0
        validated_order_items = []

        for index, item in enumerate(validated_items):
            raw_item = items_data[index] if index < len(items_data) else {}
            quantity = item.get('quantity', 1)
            item_id = item.get('daily_menu_item_id', 1)

            price = float(raw_item.get('price') or raw_item.get(
                'unit_price') or item.get('price') or item.get('unit_price') or 0.0)

            calculated_total += price * quantity
            validated_order_items.append({
                "meal_title": f"Meal Option #{item_id}",
                "quantity": quantity,
                "price": price
            })

        final_amount = float(
            raw_total) if raw_total is not None else calculated_total

        try:
            new_order = Order(
                user_id=authenticated_user_id,
                total_amount=final_amount,
                status="Pending"
            )
            session.add(new_order)
            session.flush()

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

            if phone_number:
                try:
                    mpesa_res = initiate_stk_push(
                        phone_number, int(final_amount), new_order.id
                    )
                    print("M-Pesa response:", mpesa_res)

                    if mpesa_res.get("ResponseCode") == "0":
                        new_order.checkout_request_id = mpesa_res.get(
                            "CheckoutRequestID")
                        new_order.status = "Pending Payment"
                        session.commit()
                    else:
                        print("M-Pesa STK push was not accepted:", mpesa_res)
                except Exception as mpesa_err:
                    print("M-Pesa execution error:", mpesa_err)

            return Response(OrderSerializer(new_order, context={"request": request}).data, status=status.HTTP_201_CREATED)

        except Exception as e:
            session.rollback()
            return Response(
                {"error": f"Database transaction failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_status(request, order_id):
    session = request.db
    authenticated_user_id = getattr(request.user, 'id', request.user)

    order = (
        session.query(Order)
        .filter(Order.id == order_id, Order.user_id == authenticated_user_id)
        .first()
    )

    if not order:
        return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

    return Response({
        "id": order.id,
        "status": order.status
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def mpesa_callback(request):
    stk_callback = request.data.get("Body", {}).get("stkCallback", {})
    result_code = stk_callback.get("ResultCode")
    checkout_request_id = stk_callback.get("CheckoutRequestID")

    print("M-Pesa callback received:", request.data)

    session = request.db

    order = (
        session.query(Order)
        .filter(Order.checkout_request_id == checkout_request_id)
        .first()
    )

    if order:
        order.status = "Paid" if result_code == 0 else "Payment Failed"
        session.commit()
    else:
        print("No matching order found for checkout_request_id:",
              checkout_request_id)

    return Response({"ResultCode": 0, "ResultDesc": "Accepted"}, status=status.HTTP_200_OK)
