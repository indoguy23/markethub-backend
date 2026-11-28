from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    order_number = serializers.UUIDField(
        source="order.order_number",
        read_only=True
    )

    class Meta:
        model = Payment
        fields = [
            "id",
            "order",
            "order_number",
            "payment_method",
            "amount",
            "currency",
            "status",
            "gateway_order_id",
            "gateway_payment_id",
            "failure_reason",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "order_number",
            "amount",
            "currency",
            "status",
            "gateway_order_id",
            "gateway_payment_id",
            "failure_reason",
            "created_at",
            "updated_at",
        ]