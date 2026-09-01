from rest_framework import serializers
from .models import DailyMenu, DailyMenuItem, MealOption, Meal, Order


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
    
    name = serializers.CharField(write_only=True, required=False)
    caterer_id = serializers.IntegerField(read_only=True)

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
        extra_kwargs = {
            'title': {'required': False},
            'category': {'required': False, 'allow_null': True, 'allow_blank': True},
            'description': {'required': False, 'allow_null': True, 'allow_blank': True},
            'image_url': {'required': False, 'allow_null': True, 'allow_blank': True},
        }

    def validate(self, attrs):
      
        if 'name' in attrs and 'title' not in attrs:
            attrs['title'] = attrs.pop('name')
        return attrs

    def create(self, validated_data):

        request = self.context.get('request')
        user = getattr(request, 'user', None) if request else None
        caterer_id = user.id if user and user.is_authenticated else 1

        return MealOption.objects.create(caterer_id=caterer_id, **validated_data)


class DailyMenuSerializer(serializers.ModelSerializer):
    caterer_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = DailyMenu
        fields = ['id', 'caterer_id', 'menu_date']

    def create(self, validated_data):
        request = self.context.get('request')
        user = getattr(request, 'user', None) if request else None
        caterer_id = user.id if user and user.is_authenticated else 1

        return DailyMenu.objects.create(caterer_id=caterer_id, **validated_data)


class DailyMenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyMenuItem
        fields = ['id', 'daily_menu', 'meal_option']


class DailyMenuWithItemsSerializer(serializers.ModelSerializer):
    meals = serializers.SerializerMethodField()

    class Meta:
        model = DailyMenu
        fields = ['id', 'caterer_id', 'menu_date', 'meals']

    def get_meals(self, menu):
        # Django ORM relationship retrieval
        items = DailyMenuItem.objects.filter(
            daily_menu=menu).select_related('meal_option')
        result = []
        for item in items:
            meal = item.meal_option
            if meal:
                result.append({
                    "item_id": item.id,
                    "meal_option_id": meal.id,
                    "title": meal.title,
                    "category": meal.category,
                    "price": meal.price,
                    "description": meal.description,
                    "image_url": meal.image_url,
                })
        return result
