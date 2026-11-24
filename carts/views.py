
from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsCustomer

from products.models import Product
from .models import Cart, CartItem
from .serializers import CartSerializer


class CartView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    def get(self, request):
        cart, created = Cart.objects.get_or_create(
            user=request.user
        )

        serializer = CartSerializer(cart)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class AddCartItemView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    @transaction.atomic
    def post(self, request):
        product_id = request.data.get("product_id")
        quantity = request.data.get("quantity", 1)

        # Validate product ID
        if not product_id:
            return Response(
                {"error": "Product ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate quantity
        try:
            if isinstance(quantity, bool):
                raise ValueError

            quantity = int(quantity)

            if quantity < 1:
                raise ValueError

        except (ValueError, TypeError):
            return Response(
                {"error": "Quantity must be a positive integer."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Retrieve active product and lock its row
        product = get_object_or_404(
            Product.objects.select_for_update(),
            id=product_id,
            is_active=True
        )

        # Get or create customer cart
        cart, created = Cart.objects.get_or_create(
            user=request.user
        )

        # Check whether product already exists in cart
        cart_item = CartItem.objects.select_for_update().filter(
            cart=cart,
            product=product
        ).first()

        new_quantity = quantity

        if cart_item:
            new_quantity += cart_item.quantity

        # Validate available stock
        if new_quantity > product.stock:
            return Response(
                {
                    "error": "Requested quantity exceeds available stock.",
                    "available_stock": product.stock
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create or update cart item
        if cart_item:
            cart_item.quantity = new_quantity
            cart_item.save()
        else:
            CartItem.objects.create(
                cart=cart,
                product=product,
                quantity=quantity
            )

        # Return updated cart
        cart.refresh_from_db()

        serializer = CartSerializer(cart)

        return Response(
            {
                "message": "Product added to cart successfully.",
                "cart": serializer.data
            },
            status=status.HTTP_200_OK
        )


class CartItemDetailView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    def get_cart_item(self, request, pk):
        return get_object_or_404(
            CartItem.objects.select_related(
                "cart",
                "product"
            ),
            id=pk,
            cart__user=request.user
        )

    @transaction.atomic
    def patch(self, request, pk):
        cart_item = self.get_cart_item(request, pk)

        quantity = request.data.get("quantity")

        try:
            if isinstance(quantity, bool):
                raise ValueError

            quantity = int(quantity)

            if quantity < 1:
                raise ValueError

        except (ValueError, TypeError):
            return Response(
                {"error": "Quantity must be a positive integer."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Lock product before stock validation
        product = Product.objects.select_for_update().get(
            id=cart_item.product_id
        )

        if quantity > product.stock:
            return Response(
                {
                    "error": "Requested quantity exceeds available stock.",
                    "available_stock": product.stock
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item.quantity = quantity
        cart_item.save()

        serializer = CartSerializer(cart_item.cart)

        return Response(
            {
                "message": "Cart quantity updated successfully.",
                "cart": serializer.data
            },
            status=status.HTTP_200_OK
        )

    def delete(self, request, pk):
        cart_item = self.get_cart_item(request, pk)
        cart_item.delete()

        return Response(
            {"message": "Product removed from cart successfully."},
            status=status.HTTP_200_OK
        )
