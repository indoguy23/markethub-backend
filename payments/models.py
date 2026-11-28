from django.db import models
from orders.models import Order


class Payment(models.Model):
    
    class PaymentMethod(models.TextChoices):
        MOCK = "mock", "Mock Online Payment"
        RAZORPAY = "razorpay", "Razorpay"
        COD = "cod", "Cash on Delivery"
    
    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESSFUL = "successful", "Successful"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    order = models.ForeignKey(
        Order, on_delete=models.PROTECT, related_name = "payments"
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    currency = models.CharField(
        max_length=3,
        default="INR"
    )

    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )

    gateway_order_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True
    )

    gateway_payment_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True
    )

    gateway_signature = models.CharField(
        max_length=500,
        blank=True
    )

    failure_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment #{self.id} - {self.status}"