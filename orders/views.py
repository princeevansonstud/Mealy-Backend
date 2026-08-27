from django.shortcuts import render

# Create your views here.
import json
from datetime import date, datetime

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from config.db import SessionLocal
from orders.models import Order, OrderItem
from meals.models import Meal


# View all orders
def order_list(request):
    if request.method != "GET":
        return JsonResponse(
            {"error": "Method not allowed"},
            status=405
        )

    db = SessionLocal()

    try:
        orders = db.query(Order).order_by(
            Order.created_at.desc()
        ).all()

        result = []

        for order in orders:
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

            result.append({
                "id": order.id,
                "customer_id": order.customer_id,
                "status": order.status,
                "total_amount": order.total_amount,
                "created_at": order.created_at.isoformat(),
                "items": items
            })

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

        return JsonResponse({
            "id": order.id,
            "customer_id": order.customer_id,
            "status": order.status,
            "total_amount": order.total_amount,
            "created_at": order.created_at.isoformat(),
            "items": items
        })

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

    allowed_statuses = [
        "Pending",
        "Preparing",
        "Completed",
        "Cancelled"
    ]

    if new_status not in allowed_statuses:
        return JsonResponse({
            "error": "Invalid status",
            "allowed_statuses": allowed_statuses
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
        today = date.today()

        orders = db.query(Order).filter(
            Order.status == "Completed"
        ).all()

        today_orders = [
            order for order in orders
            if order.created_at.date() == today
        ]

        total_earnings = sum(
            order.total_amount
            for order in today_orders
        )

        total_orders = len(today_orders)

        average_order_value = (
            total_earnings / total_orders
            if total_orders > 0
            else 0
        )

        return JsonResponse({
            "date": today.isoformat(),
            "total_earnings": round(total_earnings, 2),
            "total_orders": total_orders,
            "average_order_value": round(
                average_order_value,
                2
            )
        })

    finally:
        db.close()