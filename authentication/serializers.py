from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError

from rest_framework import serializers
from sqlalchemy import func, select

from .jwt import create_token_pair
from .models import User


class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    password_confirm = serializers.CharField(
        write_only=True
    )

    def validate_email(self, value):
        email = value.strip().lower()

        session = self.context["request"].db
        exists = session.scalar(
            select(User.id).where(func.lower(User.email) == email).limit(1)
        )
        if exists is not None:
            raise serializers.ValidationError(
                "A user with this email already exists."
            )

        return email

    def validate(self, attrs):
        password = attrs.get("password")
        password_confirm = attrs.get("password_confirm")

        if password != password_confirm:
            raise serializers.ValidationError({
                "password_confirm": "Passwords do not match."
            })

        try:
            password_validation.validate_password(
                password,
                user=None
            )
        except ValidationError as error:
            raise serializers.ValidationError({
                "password": error.messages
            })

        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")

        password = validated_data.pop("password")

        user = User.create(password=password, role="customer", **validated_data)
        session = self.context["request"].db
        session.add(user)
        session.flush()

        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email", "").strip().lower()
        password = attrs.get("password")

        session = self.context["request"].db
        user = session.scalar(select(User).where(func.lower(User.email) == email))
        if user is None or not user.check_password(password):
            raise serializers.ValidationError(
                "Invalid email or password."
            )

        if not user.is_active:
            raise serializers.ValidationError(
                "This account is inactive."
            )

        access, refresh = create_token_pair(user, session)

        return {
            "user": user,
            "access": access,
            "refresh": refresh,
        }
