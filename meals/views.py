import sys
import traceback
from datetime import date
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from .permissions import IsCaterer
from .models import Meal, Order, DailyMenu, MealOption
from .serializers import (
    DailyMenuSerializer,
    DailyMenuWithItemsSerializer,
    DailyMenuItemSerializer,
    MealOptionSerializer,
    MealSerializer,
    OrderSerializer,
)


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


class MealOptionListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permission() for permission in [AllowAny]]
        return [permission() for permission in [IsAuthenticated, IsCaterer]]

    def get(self, request):
        meals = MealOption.objects.all()
        serializer = MealOptionSerializer(
            meals, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = MealOptionSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            meal = serializer.save()
            return Response(
                MealOptionSerializer(meal, context={"request": request}).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DailyMenuListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsCaterer]

    def post(self, request):
        serializer = DailyMenuSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            menu = serializer.save()
            return Response(
                DailyMenuSerializer(menu, context={"request": request}).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DailyMenuTodayView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        menu = DailyMenu.objects.filter(menu_date=date.today()).first()
        if menu is None:
            return Response(
                {"message": "No menu found for today."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = DailyMenuWithItemsSerializer(
            menu, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class DailyMenuItemCreateView(APIView):
    permission_classes = [IsAuthenticated, IsCaterer]

    def post(self, request):
        serializer = DailyMenuItemSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            item = serializer.save()
            return Response(
                DailyMenuItemSerializer(
                    item, context={"request": request}).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MealOptionDetailView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permission() for permission in [AllowAny]]
        return [permission() for permission in [IsAuthenticated, IsCaterer]]

    def get_object(self, pk):
        try:
            return MealOption.objects.get(pk=pk)
        except MealOption.DoesNotExist:
            return None

    def get(self, request, pk):
        meal = self.get_object(pk)
        if not meal:
            return Response({"error": "Meal option not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            MealOptionSerializer(meal, context={"request": request}).data,
            status=status.HTTP_200_OK
        )

    def put(self, request, pk):
        meal = self.get_object(pk)
        if not meal:
            return Response(
                {"error": f"Meal option {pk} not found in database"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = MealOptionSerializer(
            meal, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            updated_meal = serializer.save()
            return Response(
                MealOptionSerializer(updated_meal, context={
                                     "request": request}).data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        return self.put(request, pk)

    def delete(self, request, pk):
        meal = self.get_object(pk)
        if not meal:
            return Response({"error": "Meal option not found"}, status=status.HTTP_404_NOT_FOUND)

        meal.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
