from unittest.mock import patch

from django.test import Client, TestCase, override_settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from config.db import Base
from meals.models import Meal
from orders.models import Order, OrderItem


class OrderApiTests(TestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.engine = create_engine(
			"sqlite://",
			connect_args={"check_same_thread": False},
			poolclass=StaticPool
		)
		Base.metadata.create_all(bind=cls.engine)
		cls.session_factory = sessionmaker(bind=cls.engine)

	def setUp(self):
		self.session = self.session_factory()
		self.session.query(OrderItem).delete()
		self.session.query(Order).delete()
		self.session.query(Meal).delete()
		self.session.commit()

		self.meal = Meal(title="Test Meal", price=15.50)
		self.session.add(self.meal)
		self.session.commit()
		self.session.refresh(self.meal)

		self.session_patch = patch(
			"orders.views.SessionLocal",
			side_effect=self.session_factory
		)
		self.session_patch.start()
		self.client = Client()

	def tearDown(self):
		self.session_patch.stop()
		self.session.close()

	@override_settings(ALLOWED_HOSTS=["testserver"])
	def test_create_order_calculates_total_from_meal_price(self):
		response = self.client.post(
			"/api/orders/",
			{
				"customer_id": 4,
				"items": [{"meal_id": self.meal.id, "quantity": 2}]
			},
			content_type="application/json"
		)

		self.assertEqual(response.status_code, 201)
		self.assertEqual(response.json()["total_amount"], 31.0)
		self.assertEqual(response.json()["items"][0]["subtotal"], 31.0)

	@override_settings(ALLOWED_HOSTS=["testserver"])
	def test_create_order_accepts_frontend_item_shape(self):
		response = self.client.post(
			"/api/orders/",
			{
				"userId": "customer@example.com",
				"items": [{"name": "Test Meal", "price": 999, "quantity": 1}]
			},
			content_type="application/json"
		)

		self.assertEqual(response.status_code, 201)
		self.assertEqual(response.json()["totalAmount"], 15.5)
		self.assertEqual(response.json()["items"][0]["name"], "Test Meal")

	@override_settings(ALLOWED_HOSTS=["testserver"])
	def test_earnings_counts_completed_orders_only(self):
		completed = Order(customer_id=1, status="Completed", total_amount=31)
		pending = Order(customer_id=2, status="Pending", total_amount=99)
		cancelled = Order(customer_id=3, status="Cancelled", total_amount=50)
		delivered = Order(customer_id=4, status="Delivered", total_amount=15.50)
		completed.items.append(OrderItem(
			meal_id=self.meal.id,
			quantity=2,
			unit_price=15.50,
			subtotal=31
		))
		delivered.items.append(OrderItem(
			meal_id=self.meal.id,
			quantity=1,
			unit_price=15.50,
			subtotal=15.50
		))
		self.session.add_all([completed, pending, cancelled, delivered])
		self.session.commit()

		response = self.client.get("/api/orders/earnings/")

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()["total_earnings"], 46.5)
		self.assertEqual(response.json()["total_orders"], 2)
		self.assertEqual(response.json()["total_meals_sold"], 3)

		invalid_date = self.client.get(
			"/api/orders/earnings/?date=28-08-2026"
		)
		self.assertEqual(invalid_date.status_code, 400)

# Create your tests here.
