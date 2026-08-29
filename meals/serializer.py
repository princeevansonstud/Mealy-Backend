from rest_framework import serializers
from .models import Meal, Order, DailyMenu, DailyMenuItem, MealOption


class MealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meal
        fields = [
            'id',
            'name',
            'description',
            'price',
            'category',
            'is_on_daily_menu',
            'created_at',
        ]


class OrderSerializer(serializers.ModelSerializer):
    customerName = serializers.CharField(
        source='customer_name', required=False, allow_blank=True
    )
    totalAmount = serializers.DecimalField(
        source='total_amount', max_digits=10, decimal_places=2, required=False
    )

    class Meta:
        model = Order
        fields = ['id', 'customerName', 'totalAmount', 'status', 'created_at']


class MealOptionSerializer(serializers.ModelSerializer):
    caterer_id = serializers.IntegerField(source='caterer.id', read_only=True)
    name = serializers.CharField(source='title', required=False)

    class Meta:
        model = MealOption
        fields = [
            'id',
            'caterer_id',
            'title',
            'name',
            'category',
            'price',
            'description',
            'image_url',
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        caterer = getattr(request, 'user', None) if request else None

        if 'title' not in validated_data and 'name' in validated_data:
            validated_data['title'] = validated_data.pop('name')

        if caterer and caterer.is_authenticated:
            return MealOption.objects.create(caterer=caterer, **validated_data)

        return MealOption.objects.create(**validated_data)

    def update(self, instance, validated_data):
        if 'title' not in validated_data and 'name' in validated_data:
            validated_data['title'] = validated_data.pop('name')

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class DailyMenuSerializer(serializers.ModelSerializer):
    caterer_id = serializers.IntegerField(source='caterer.id', read_only=True)

    class Meta:
        model = DailyMenu
        fields = ['id', 'caterer_id', 'menu_date']

    def create(self, validated_data):
        request = self.context.get('request')
        caterer = getattr(request, 'user', None) if request else None

        if caterer and caterer.is_authenticated:
            return DailyMenu.objects.create(caterer=caterer, **validated_data)

        return DailyMenu.objects.create(**validated_data)


class DailyMenuItemSerializer(serializers.ModelSerializer):
    daily_menu_id = serializers.IntegerField(write_only=True)
    meal_option_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = DailyMenuItem
        fields = ['id', 'daily_menu_id', 'meal_option_id']


class DailyMenuWithItemsSerializer(serializers.ModelSerializer):
    caterer_id = serializers.IntegerField(source='caterer.id', read_only=True)
    meals = serializers.SerializerMethodField()

    class Meta:
        model = DailyMenu
        fields = ['id', 'caterer_id', 'menu_date', 'meals']

    def get_meals(self, menu):
        items = DailyMenuItem.objects.filter(daily_menu=menu).select_related(
            'meal_option'
        )
        result = []
        for item in items:
            meal = item.meal_option
            if meal:
                result.append({
                    'item_id': item.id,
                    'meal_option_id': meal.id,
                    'title': meal.title,
                    'category': meal.category,
                    'price': float(meal.price),
                    'description': meal.description,
                    'image_url': meal.image_url,
                })
        return result
