
from django.contrib.auth.models import User
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import UserProfile
from categories.models import Category
from products.models import Product

from .models import Cart, CartItem


class CartAPITests(APITestCase):

    def setUp(self):
        # Create customer
        self.user = User.objects.create_user(
            username="cart_customer",
            password="TestPassword@123"
        )

        UserProfile.objects.create(
            user=self.user,
            role=UserProfile.Role.CUSTOMER
        )

        self.client.force_authenticate(user=self.user)

        # Create category
        self.category = Category.objects.create(
            name="Electronics",
            description="Electronic devices"
        )

        # Create product
        self.product = Product.objects.create(
            category=self.category,
            name="Wireless Headphones",
            description="Bluetooth headphones",
            price="1999.00",
            stock=25,
            is_active=True
        )

        # Create cart
        self.cart = Cart.objects.create(
            user=self.user
        )

        # Create cart item
        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )

        # API URLs
        self.cart_url = reverse("cart-detail")
        self.add_item_url = reverse("cart-add-item")
        self.item_detail_url = reverse(
            "cart-item-detail",
            args=[self.cart_item.id]
        )

    def test_get_cart(self):
        response = self.client.get(self.cart_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_add_product_to_cart(self):
        response = self.client.post(
            self.add_item_url,
            {
                "product_id": self.product.id,
                "quantity": 3
            }
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.cart_item.refresh_from_db()

        self.assertEqual(self.cart_item.quantity, 5)

    def test_add_existing_product_increases_quantity(self):
        response = self.client.post(
            self.add_item_url,
            {
                "product_id": self.product.id,
                "quantity": 2
            }
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.cart_item.refresh_from_db()

        self.assertEqual(self.cart_item.quantity, 4)

        self.assertEqual(
            CartItem.objects.filter(cart=self.cart).count(),
            1
        )

    def test_add_product_with_invalid_quantity(self):
        response = self.client.post(
            self.add_item_url,
            {
                "product_id": self.product.id,
                "quantity": 0
            }
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_add_product_exceeding_stock(self):
        response = self.client.post(
            self.add_item_url,
            {
                "product_id": self.product.id,
                "quantity": 30
            }
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_update_cart_item_quantity(self):
        response = self.client.patch(
            self.item_detail_url,
            {"quantity": 5}
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.cart_item.refresh_from_db()

        self.assertEqual(self.cart_item.quantity, 5)

    def test_remove_cart_item(self):
        response = self.client.delete(
            self.item_detail_url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertFalse(
            CartItem.objects.filter(
                id=self.cart_item.id
            ).exists()
        )

    def test_customer_cannot_access_another_customers_cart_item(self):
        another_user = User.objects.create_user(
            username="another_customer",
            password="TestPassword@123"
        )

        UserProfile.objects.create(
            user=another_user,
            role=UserProfile.Role.CUSTOMER
        )

        another_cart = Cart.objects.create(
            user=another_user
        )

        another_cart_item = CartItem.objects.create(
            cart=another_cart,
            product=self.product,
            quantity=1
        )

        response = self.client.patch(
            reverse(
                "cart-item-detail",
                args=[another_cart_item.id]
            ),
            {"quantity": 3}
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )
