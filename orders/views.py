
from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsCustomer
from carts.models import Cart, CartItem
from products.models import Product

from .models import Order, OrderItem
from .serializers import OrderSerializer


class OrderListCreateView(APIView):

    permission_classes = [IsAuthenticated, IsCustomer]

    def get(self, request):
        orders = Order.objects.filter(
            user=request.user
        ).prefetch_related("items").order_by("-created_at")

        serializer = OrderSerializer(orders, many=True)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @transaction.atomic
    def post(self, request):

        # Validate shipping details
        serializer = OrderSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        # Lock the customer's cart
        cart = Cart.objects.select_for_update().filter(
            user=request.user
        ).first()

        if not cart:
            return Response(
                {"error": "Your cart is empty."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Lock cart items
        cart_items = list(
            CartItem.objects.select_for_update()
            .filter(cart=cart)
            .order_by("id")
        )

        if not cart_items:
            return Response(
                {"error": "Your cart is empty."},
                status=status.HTTP_400_BAD_REQUEST
            )

        total_amount = Decimal("0.00")
        order_items_data = []

        # Validate products and calculate total
        for cart_item in cart_items:

            product = Product.objects.select_for_update().get(
                id=cart_item.product_id
            )

            if not product.is_active:
                return Response(
                    {
                        "error": f"{product.name} is no longer available."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            if cart_item.quantity > product.stock:
                return Response(
                    {
                        "error": f"Insufficient stock for {product.name}.",
                        "available_stock": product.stock
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            item_total = product.price * cart_item.quantity
            total_amount += item_total

            order_items_data.append({
                "product": product,
                "product_name": product.name,
                "price": product.price,
                "quantity": cart_item.quantity
            })

        # Create the order
        order = Order.objects.create(
            user=request.user,
            total_amount=total_amount,
            **serializer.validated_data
        )

        # Create order items and update stock
        for item_data in order_items_data:

            OrderItem.objects.create(
                order=order,
                **item_data
            )

            product = item_data["product"]
            product.stock -= item_data["quantity"]
            product.save(update_fields=["stock", "updated_at"])

        # Clear purchased cart items
        CartItem.objects.filter(cart=cart).delete()

        response_serializer = OrderSerializer(order)

        return Response(
            {
                "message": "Order placed successfully.",
                "order": response_serializer.data
            },
            status=status.HTTP_201_CREATED
        )


class OrderDetailView(APIView):

    permission_classes = [IsAuthenticated, IsCustomer]

    def get(self, request, pk):

        order = get_object_or_404(
            Order.objects.prefetch_related("items"),
            id=pk,
            user=request.user
        )

        serializer = OrderSerializer(order)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )
