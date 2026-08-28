from django.shortcuts import render

# Create your views here.
import json
from datetime import date, datetime, timedelta

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from config.db import SessionLocal
from orders.models import Order, OrderItem
from meals.models import Meal

ALLOWED_STATUSES = [
    "Pending",
    "Preparing",
    "Completed",
    "Delivered",
    "Cancelled"
]
EARNING_STATUSES = ("Completed", "Delivered")


def _serialize_order(order, db):
    items = []

    for item in order.items:
        meal = db.query(Meal).filter(
            Meal.id == item.meal_id
        ).first()

        items.append({
            "id": item.id,
            "meal_id": item.meal_id,
            "meal_name": meal.title if meal else "Unknown meal",
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "subtotal": item.subtotal
        })

    return {
        "id": order.id,
        "customer_id": order.customer_id,
        "status": order.status,
        "total_amount": order.total_amount,
        "created_at": order.created_at.isoformat(),
        "items": items
    }


@csrf_exempt
def create_order(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    raw_items = data.get("items")
    if not isinstance(raw_items, list) or not raw_items:
        return JsonResponse({"error": "items must be a non-empty list"}, status=400)

    db = SessionLocal()

    try:
        order_items = []
        total_amount = 0

        for raw_item in raw_items:
            meal_id = raw_item.get("meal_id") if isinstance(raw_item, dict) else None
            quantity = raw_item.get("quantity") if isinstance(raw_item, dict) else None

            if not isinstance(meal_id, int) or not isinstance(quantity, int) or quantity < 1:
                return JsonResponse({
                    "error": "Each item requires an integer meal_id and positive integer quantity"
                }, status=400)

            meal = db.query(Meal).filter(Meal.id == meal_id).first()
            if not meal:
                return JsonResponse({"error": f"Meal {meal_id} not found"}, status=404)

            subtotal = round(meal.price * quantity, 2)
            total_amount += subtotal
            order_items.append(OrderItem(
                meal_id=meal.id,
                quantity=quantity,
                unit_price=meal.price,
                subtotal=subtotal
            ))

        order = Order(
            customer_id=data.get("customer_id"),
            total_amount=round(total_amount, 2),
            items=order_items
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        return JsonResponse(_serialize_order(order, db), status=201)
    except (TypeError, ValueError):
        db.rollback()
        return JsonResponse({"error": "Invalid order data"}, status=400)
    finally:
        db.close()


# View all orders
def order_list(request):
    if request.method == "POST":
        return create_order(request)

    if request.method != "GET":
        return JsonResponse(
            {"error": "Method not allowed"},
            status=405
        )

    db = SessionLocal()

    try:
        query = db.query(Order)
        customer_id = request.GET.get("customer_id")

        if customer_id is not None:
            try:
                customer_id = int(customer_id)
            except ValueError:
                return JsonResponse(
                    {"error": "customer_id must be an integer"},
                    status=400
                )

            query = query.filter(Order.customer_id == customer_id)

        orders = query.order_by(Order.created_at.desc()).all()

        result = [_serialize_order(order, db) for order in orders]

        return JsonResponse(result, safe=False)

    finally:
        db.close()


# View one order
def order_detail(request, order_id):
    if request.method != "GET":
        return JsonResponse(
            {"error": "Method not allowed"},
            status=405
        )

    db = SessionLocal()

    try:
        order = db.query(Order).filter(
            Order.id == order_id
        ).first()

        if not order:
            return JsonResponse(
                {"error": "Order not found"},
                status=404
            )

        return JsonResponse(_serialize_order(order, db))

    finally:
        db.close()


# Update order status
@csrf_exempt
def update_order_status(request, order_id):
    if request.method != "PUT":
        return JsonResponse(
            {"error": "Method not allowed"},
            status=405
        )

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Invalid JSON"},
            status=400
        )

    new_status = data.get("status")

    if new_status not in ALLOWED_STATUSES:
        return JsonResponse({
            "error": "Invalid status",
            "allowed_statuses": ALLOWED_STATUSES
        }, status=400)

    db = SessionLocal()

    try:
        order = db.query(Order).filter(
            Order.id == order_id
        ).first()

        if not order:
            return JsonResponse(
                {"error": "Order not found"},
                status=404
            )

        order.status = new_status
        order.updated_at = datetime.utcnow()

        db.commit()

        return JsonResponse({
            "message": "Order status updated successfully",
            "order": {
                "id": order.id,
                "status": order.status,
                "total_amount": order.total_amount
            }
        })

    finally:
        db.close()


# View today's earnings
def earnings(request):
    if request.method != "GET":
        return JsonResponse(
            {"error": "Method not allowed"},
            status=405
        )

    db = SessionLocal()

    try:
        requested_date = request.GET.get("date")
        if requested_date:
            try:
                earnings_date = date.fromisoformat(requested_date)
            except ValueError:
                return JsonResponse({
                    "error": "date must use YYYY-MM-DD format"
                }, status=400)
        else:
            earnings_date = date.today()

        start = datetime.combine(earnings_date, datetime.min.time())
        end = start + timedelta(days=1)

        today_orders = db.query(Order).filter(
            Order.status.in_(EARNING_STATUSES),
            Order.created_at >= start,
            Order.created_at < end
        ).all()

        total_earnings = sum(
            order.total_amount
            for order in today_orders
        )

        total_orders = len(today_orders)
        total_meals_sold = sum(
            item.quantity
            for order in today_orders
            for item in order.items
        )

        average_order_value = (
            total_earnings / total_orders
            if total_orders > 0
            else 0
        )

        return JsonResponse({
            "date": earnings_date.isoformat(),
            "total_earnings": round(total_earnings, 2),
            "total_orders": total_orders,
            "total_meals_sold": total_meals_sold,
            "average_order_value": round(
                average_order_value,
                2
            )
        })

    finally:
        db.close()