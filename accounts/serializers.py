from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers

from .models import UserProfile



class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    phone_number = serializers.CharField(required=False, allow_blank=True)

    role = serializers.ChoiceField(choices=UserProfile.Role.choices, default=UserProfile.Role.CUSTOMER)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "phone_number",
            "role",
        ]

    @transaction.atomic
    def create(self, validated_data):
        phone_number = validated_data.pop("phone_number", "")
        role = validated_data.pop("role", UserProfile.Role.CUSTOMER)
        password = validated_data.pop("password")

        user = User.objects.create_user(
            password=password,
            **validated_data
        )

        UserProfile.objects.create(
            user=user,
            phone_number=phone_number,
            role=role
        )

        return user