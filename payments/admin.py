from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "payment_method",
        "amount",
        "currency",
        "status",
        "created_at",
    )

    list_filter = (
        "payment_method",
        "status",
        "currency",
        "created_at",
    )

    search_fields = (
        "gateway_order_id",
        "gateway_payment_id",
        "order__order_number",
        "order__user__username",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)