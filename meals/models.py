from django.conf import settings
from django.db import models


class Meal(models.Model):
    CATEGORY_CHOICES = [
        ('VEGAN', 'Vegan'),
        ('BEEF', 'Beef'),
        ('PORK', 'Pork'),
        ('CHICKEN', 'Chicken'),
        ('CHEESE', 'Cheese'),
        ('GREENS', 'Greens'),
    ]

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, default='BEEF')
    is_on_daily_menu = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('preparing', 'Preparing'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    customer_name = models.CharField(
        max_length=255, blank=True, default='Guest')
    total_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name} ({self.status})"


class MealOption(models.Model):
    caterer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='meal_options'
    )
    title = models.CharField(max_length=100)
    category = models.CharField(max_length=50, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, blank=True, null=True)
    image_url = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.title


class DailyMenu(models.Model):
    caterer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='daily_menus'
    )
    menu_date = models.DateField()

    def __str__(self):
        return f"Menu for {self.menu_date}"


class DailyMenuItem(models.Model):
    daily_menu = models.ForeignKey(
        DailyMenu,
        on_delete=models.CASCADE,
        related_name='items'
    )
    meal_option = models.ForeignKey(
        MealOption,
        on_delete=models.CASCADE,
        related_name='daily_menu_items'
    )

    def __str__(self):
        return f"{self.meal_option.title} - {self.daily_menu.menu_date}"
