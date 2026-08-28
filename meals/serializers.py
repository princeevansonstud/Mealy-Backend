from rest_framework import serializers

from .models import DailyMenu, DailyMenuItem, MealOption


class MealOptionSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    caterer_id = serializers.IntegerField()
    title = serializers.CharField(max_length=100)
    price = serializers.FloatField()
    description = serializers.CharField(max_length=255, required=False, allow_null=True)
    image_url = serializers.CharField(max_length=255, required=False, allow_null=True)

    def create(self, validated_data):
        session = self.context["request"].db
        meal = MealOption(**validated_data)
        session.add(meal)
        session.flush()
        return meal


class DailyMenuSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    caterer_id = serializers.IntegerField()
    menu_date = serializers.DateField()

    def create(self, validated_data):
        session = self.context["request"].db
        menu = DailyMenu(**validated_data)
        session.add(menu)
        session.flush()
        return menu


class DailyMenuItemSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    daily_menu_id = serializers.IntegerField()
    meal_option_id = serializers.IntegerField()

    def create(self, validated_data):
        session = self.context["request"].db
        item = DailyMenuItem(**validated_data)
        session.add(item)
        session.flush()
        return item


class DailyMenuWithItemsSerializer(serializers.Serializer):
    """Read-only nested view: a daily menu with its meal options attached."""
    id = serializers.IntegerField(read_only=True)
    caterer_id = serializers.IntegerField(read_only=True)
    menu_date = serializers.DateField(read_only=True)
    meals = serializers.SerializerMethodField()

    def get_meals(self, menu):
        session = self.context["request"].db
        items = (
            session.query(DailyMenuItem)
            .filter(DailyMenuItem.daily_menu_id == menu.id)
            .all()
        )
        result = []
        for item in items:
            meal = session.get(MealOption, item.meal_option_id)
            if meal:
                result.append({
                    "item_id": item.id,
                    "meal_option_id": meal.id,
                    "title": meal.title,
                    "price": meal.price,
                    "description": meal.description,
                    "image_url": meal.image_url,
                })
        return result