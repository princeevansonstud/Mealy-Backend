from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from rest_framework import serializers

from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    password_confirm = serializers.CharField(
        write_only=True
    )

    class Meta:
        model = User
        fields = [
            "name",
            "email",
            "password",
            "password_confirm",
            "role",
        ]

    def validate_email(self, value):
        email = value.strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )

        return email

    def validate_role(self, value):
        allowed_roles = ["customer", "caterer"]

        if value not in allowed_roles:
            raise serializers.ValidationError(
                "Role must be either customer or caterer."
            )

        return value

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

        user = User.objects.create_user(
            password=password,
            **validated_data
        )

        return user