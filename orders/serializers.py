from rest_framework import serializers
from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "product_name",
            "price",
            "quantity",
        ]

        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "user",
            "username",
            "items",
            "total_amount",
            "status",
            "shipping_address",
            "shipping_city",
            "shipping_state",
            "shipping_postal_code",
            "shipping_phone",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "order_number",
            "user",
            "username",
            "items",
            "total_amount",
            "status",
            "created_at",
            "updated_at",
        ]
