
from decimal import Decimal

from django.contrib.auth.models import User

from rest_framework.test import APITestCase
from rest_framework import status

from accounts.models import UserProfile
from categories.models import Category
from products.models import Product
from carts.models import Cart, CartItem
from .models import Order, OrderItem


class OrderAPITestCase(APITestCase):

    def setUp(self):
        # Create customer
        self.user = User.objects.create_user(
            username="customer1",
            email="customer@example.com",
            password="TestPassword123"
        )

        UserProfile.objects.create(
            user=self.user,
            role=UserProfile.Role.CUSTOMER
        )

        self.client.force_authenticate(user=self.user)

        # Create category
        self.category = Category.objects.create(
            name="Electronics",
            description="Electronic products"
        )

        # Create product
        self.product = Product.objects.create(
            category=self.category,
            name="Laptop",
            description="Test laptop",
            price=Decimal("50000.00"),
            stock=25,
            is_active=True
        )

        # Create cart and cart item
        self.cart = Cart.objects.create(user=self.user)

        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )

        self.order_url = "/api/orders/"

        self.shipping_data = {
            "shipping_address": "123 Main Street",
            "shipping_city": "Bangalore",
            "shipping_state": "Karnataka",
            "shipping_postal_code": "560001",
            "shipping_phone": "9876543210"
        }

    def test_get_orders(self):
        response = self.client.get(self.order_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_create_order_successfully(self):
        response = self.client.post(
            self.order_url,
            self.shipping_data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)

    def test_order_total_amount(self):
        self.client.post(
            self.order_url,
            self.shipping_data,
            format="json"
        )

        order = Order.objects.get(user=self.user)

        self.assertEqual(
            order.total_amount,
            Decimal("100000.00")
        )

    def test_product_stock_is_reduced(self):
        self.client.post(
            self.order_url,
            self.shipping_data,
            format="json"
        )

        self.product.refresh_from_db()

        self.assertEqual(self.product.stock, 23)

    def test_cart_is_cleared_after_order(self):
        self.client.post(
            self.order_url,
            self.shipping_data,
            format="json"
        )

        self.assertEqual(
            CartItem.objects.filter(cart=self.cart).count(),
            0
        )

    def test_order_fails_when_cart_is_empty(self):
        self.cart_item.delete()

        response = self.client.post(
            self.order_url,
            self.shipping_data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_order_fails_when_stock_is_insufficient(self):
        self.product.stock = 1
        self.product.save()

        response = self.client.post(
            self.order_url,
            self.shipping_data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertEqual(Order.objects.count(), 0)

    def test_order_fails_for_inactive_product(self):
        self.product.is_active = False
        self.product.save()

        response = self.client.post(
            self.order_url,
            self.shipping_data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertEqual(Order.objects.count(), 0)

    def test_order_detail(self):
        response = self.client.post(
            self.order_url,
            self.shipping_data,
            format="json"
        )

        order_id = response.data["order"]["id"]

        response = self.client.get(
            f"{self.order_url}{order_id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_customer_cannot_access_another_users_order(self):
        other_user = User.objects.create_user(
            username="customer2",
            password="TestPassword123"
        )

        order = Order.objects.create(
            user=other_user,
            total_amount=Decimal("100.00"),
            shipping_address="Other address",
            shipping_city="Delhi",
            shipping_state="Delhi",
            shipping_postal_code="110001",
            shipping_phone="9876543210"
        )

        response = self.client.get(
            f"{self.order_url}{order.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )
    

    def test_customer_can_cancel_pending_order(self):
        # First create an order (stock reduces from 25 to 23).
        create_response = self.client.post(
            self.order_url,
            self.shipping_data,
            format="json"
        )

        order_id = create_response.data["order"]["id"]

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 23)

        # Cancel the order.
        response = self.client.post(
            f"{self.order_url}{order_id}/cancel/"
        )

        self.product.refresh_from_db()
        order = Order.objects.get(id=order_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.assertEqual(self.product.stock, 25)

    def test_cancelled_order_does_not_restore_stock_twice(self):
        create_response = self.client.post(
            self.order_url,
            self.shipping_data,
            format="json"
        )

        order_id = create_response.data["order"]["id"]

        cancel_url = f"{self.order_url}{order_id}/cancel/"

        first_response = self.client.post(cancel_url)

        self.product.refresh_from_db()
        stock_after_first_cancellation = self.product.stock

        second_response = self.client.post(cancel_url)

        self.product.refresh_from_db()

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            second_response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(
            self.product.stock,
            stock_after_first_cancellation
        )
        self.assertEqual(self.product.stock, 25)

    def test_customer_cannot_cancel_confirmed_order(self):
        create_response = self.client.post(
            self.order_url,
            self.shipping_data,
            format="json"
        )

        order_id = create_response.data["order"]["id"]

        order = Order.objects.get(id=order_id)
        order.status = Order.Status.CONFIRMED
        order.save(update_fields=["status", "updated_at"])

        response = self.client.post(
            f"{self.order_url}{order_id}/cancel/"
        )

        self.product.refresh_from_db()

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(self.product.stock, 23)

    def test_customer_cannot_cancel_another_users_order(self):
        other_user = User.objects.create_user(
            username="cancelowner",
            password="TestPassword123"
        )

        other_order = Order.objects.create(
            user=other_user,
            total_amount=Decimal("500.00"),
            shipping_address="Other address",
            shipping_city="Delhi",
            shipping_state="Delhi",
            shipping_postal_code="110001",
            shipping_phone="9876543210"
        )

        response = self.client.post(
            f"{self.order_url}{other_order.id}/cancel/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )

        other_order.refresh_from_db()

        self.assertEqual(
            other_order.status,
            Order.Status.PENDING
        )
