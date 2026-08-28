import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from config.db import SessionLocal
from .models import Meal


def _serialize_meal(meal):
	return {
		"id": meal.id,
		"title": meal.title,
		"price": meal.price,
		"description": meal.description,
		"image_url": meal.image_url
	}


@csrf_exempt
def meal_list_create(request):
	db = SessionLocal()

	try:
		if request.method == "GET":
			meals = db.query(Meal).order_by(Meal.id).all()
			return JsonResponse(
				[_serialize_meal(meal) for meal in meals],
				safe=False
			)

		if request.method != "POST":
			return JsonResponse({"error": "Method not allowed"}, status=405)

		try:
			data = json.loads(request.body)
		except json.JSONDecodeError:
			return JsonResponse({"error": "Invalid JSON"}, status=400)

		title = data.get("title")
		price = data.get("price")
		if not title or price is None:
			return JsonResponse({
				"error": "title and price are required"
			}, status=400)

		meal = Meal(
			title=title,
			price=float(price),
			description=data.get("description"),
			image_url=data.get("image_url")
		)
		db.add(meal)
		db.commit()
		db.refresh(meal)

		return JsonResponse(_serialize_meal(meal), status=201)
	except (TypeError, ValueError):
		db.rollback()
		return JsonResponse({"error": "Invalid meal data"}, status=400)
	finally:
		db.close()
