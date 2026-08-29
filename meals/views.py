from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Meal, Order
from .serializer import MealSerializer, OrderSerializer

class MealViewSet(viewsets.ModelViewSet):
    queryset = Meal.objects.all().order_by('-created_at')
    serializer_class = MealSerializer

    @action(detail=False, methods=['get'])
    def daily_menu(self, request):
        daily_meals = Meal.objects.filter(is_on_daily_menu=True)
        serializer = self.get_serializer(daily_meals, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'])
    def toggle_daily_menu(self, request, pk=None):
        meal = self.get_object()
        meal.is_on_daily_menu = not meal.is_on_daily_menu
        meal.save()
        return Response(self.get_serializer(meal).data, status=status.HTTP_200_OK)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer
from datetime import date

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DailyMenu, MealOption
from .permissions import IsCaterer
from .serializers import (
    DailyMenuSerializer,
    DailyMenuWithItemsSerializer,
    DailyMenuItemSerializer,
    MealOptionSerializer,
)


class MealOptionListCreateView(APIView):
    def get_permissions(self):

        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated(), IsCaterer()]

    def get(self, request):
        session = request.db
        meals = session.query(MealOption).all()
        serializer = MealOptionSerializer(meals, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = MealOptionSerializer(
            data=request.data, context={"request": request})
        if serializer.is_valid():
            meal = serializer.save()
            return Response(MealOptionSerializer(meal).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DailyMenuListCreateView(APIView):

    permission_classes = [IsAuthenticated, IsCaterer]

    def post(self, request):
        serializer = DailyMenuSerializer(
            data=request.data, context={"request": request})
        if serializer.is_valid():
            menu = serializer.save()
            return Response(DailyMenuSerializer(menu).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DailyMenuTodayView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):
        session = request.db
        menu = session.query(DailyMenu).filter(
            DailyMenu.menu_date == date.today()).first()
        if menu is None:
            return Response(
                {"message": "No menu found for today."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = DailyMenuWithItemsSerializer(
            menu, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class DailyMenuItemCreateView(APIView):

    permission_classes = [IsAuthenticated, IsCaterer]

    def post(self, request):
        serializer = DailyMenuItemSerializer(
            data=request.data, context={"request": request})
        if serializer.is_valid():
            item = serializer.save()
            return Response(DailyMenuItemSerializer(item).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
