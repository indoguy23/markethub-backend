
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsCustomer
from orders.models import Order

from .models import Payment
from .serializers import PaymentSerializer
from .services.mock_gateway import MockPaymentGateway

from orders.models import Order, OrderItem
from products.models import Product


class PaymentCreateView(APIView):

    permission_classes = [IsAuthenticated, IsCustomer]

    def post(self, request):

        serializer = PaymentSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        order_id = serializer.validated_data["order"].id
        payment_method = serializer.validated_data["payment_method"]

        order = get_object_or_404(
            Order,
            id=order_id,
            user=request.user
        )

        if order.status == Order.Status.CANCELLED:
            return Response(
                {"message": "Payment cannot be created for a cancelled order."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Razorpay is not implemented in the current version.
        if payment_method != Payment.PaymentMethod.MOCK:
            return Response(
                {"message": "Only mock payments are currently supported."},
                status=status.HTTP_400_BAD_REQUEST
            )

        payment = Payment.objects.create(
            order=order,
            payment_method=payment_method,
            amount=order.total_amount,
            currency="INR",
            status=Payment.PaymentStatus.PENDING
        )

        return Response(
            {
                "message": "Payment initiated successfully.",
                "payment": PaymentSerializer(payment).data
            },
            status=status.HTTP_201_CREATED
        )



class PaymentProcessView(APIView):

    permission_classes = [IsAuthenticated, IsCustomer]

    def post(self, request, pk):

        if not settings.MOCK_PAYMENT_PROCESSING_ENABLED:
            return Response(
                {
                    "message": "Mock payment processing is available only in development."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        outcome = request.data.get("outcome", "success")

        if outcome not in ("success", "failure"):
            return Response(
                {
                    "message": "Outcome must be either 'success' or 'failure'."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():

            payment = get_object_or_404(
                Payment.objects.select_for_update(),
                id=pk,
                order__user=request.user
            )

            if payment.payment_method != Payment.PaymentMethod.MOCK:
                return Response(
                    {"message": "Only mock payments can be processed here."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if payment.status != Payment.PaymentStatus.PENDING:
                return Response(
                    {"message": "Only pending payments can be processed."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            order = Order.objects.select_for_update().get(
                id=payment.order_id
            )

            if order.status == Order.Status.CANCELLED:
                return Response(
                    {
                        "message": "Payment cannot be processed for a cancelled order."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                result = MockPaymentGateway.process_payment(
                    amount=payment.amount,
                    outcome=outcome
                )
            except ValueError as error:
                return Response(
                    {"message": str(error)},
                    status=status.HTTP_400_BAD_REQUEST
                )

            payment.gateway_payment_id = result["transaction_id"]

            if result["status"] == "successful":

                payment.status = Payment.PaymentStatus.SUCCESSFUL
                payment.failure_reason = ""

                order.status = Order.Status.CONFIRMED
                order.save(update_fields=["status", "updated_at"])

            else:

                payment.status = Payment.PaymentStatus.FAILED
                payment.failure_reason = result["message"]

                # Restore stock for every item in the failed order.
                order_items = OrderItem.objects.select_for_update().filter(
                    order=order
                ).order_by("product_id")

                for order_item in order_items:

                    product = Product.objects.select_for_update().get(
                        id=order_item.product_id
                    )

                    product.stock += order_item.quantity

                    product.save(
                        update_fields=["stock", "updated_at"]
                    )

                # Cancel the order so its stock cannot be restored twice.
                order.status = Order.Status.CANCELLED

                order.save(
                    update_fields=["status", "updated_at"]
                )

            payment.save()

        return Response(
            {
                "message": result["message"],
                "payment": PaymentSerializer(payment).data
            },
            status=status.HTTP_200_OK
        )

