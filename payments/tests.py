
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import override_settings

from rest_framework.test import APITestCase
from rest_framework import status

from accounts.models import UserProfile
from orders.models import Order
from .models import Payment

from products.models import Product
from orders.models import Order, OrderItem


@override_settings(DEBUG=True)
class PaymentCreateTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="paymentuser",
            email="payment@example.com",
            password="TestPassword123!"
        )

        UserProfile.objects.create(
            user=self.user,
            role=UserProfile.Role.CUSTOMER
        )

        self.order = Order.objects.create(
            user=self.user,
            total_amount=Decimal("1500.00"),
            shipping_address="123 Main Street",
            shipping_city="Bangalore",
            shipping_state="Karnataka",
            shipping_postal_code="560001",
            shipping_phone="9876543210"
        )

        self.client.force_authenticate(user=self.user)

        self.url = "/api/payments/"

    def test_customer_can_create_mock_payment(self):
        response = self.client.post(
            self.url,
            {
                "order": self.order.id,
                "payment_method": Payment.PaymentMethod.MOCK
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Payment.objects.count(), 1)

        payment = Payment.objects.first()

        self.assertEqual(payment.order, self.order)
        self.assertEqual(payment.amount, Decimal("1500.00"))
        self.assertEqual(payment.status, Payment.PaymentStatus.PENDING)

    def test_payment_amount_is_calculated_by_backend(self):
        response = self.client.post(
            self.url,
            {
                "order": self.order.id,
                "payment_method": Payment.PaymentMethod.MOCK,
                "amount": "1.00"
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        payment = Payment.objects.first()
        self.assertEqual(payment.amount, Decimal("1500.00"))

    def test_customer_cannot_pay_another_users_order(self):
        another_user = User.objects.create_user(
            username="anotheruser",
            password="TestPassword123!"
        )

        another_order = Order.objects.create(
            user=another_user,
            total_amount=Decimal("500.00"),
            shipping_address="Another Street",
            shipping_city="Bangalore",
            shipping_state="Karnataka",
            shipping_postal_code="560002",
            shipping_phone="9876543211"
        )

        response = self.client.post(
            self.url,
            {
                "order": another_order.id,
                "payment_method": Payment.PaymentMethod.MOCK
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Payment.objects.count(), 0)

    def test_payment_cannot_be_created_for_cancelled_order(self):
        self.order.status = Order.Status.CANCELLED
        self.order.save()

        response = self.client.post(
            self.url,
            {
                "order": self.order.id,
                "payment_method": Payment.PaymentMethod.MOCK
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Payment.objects.count(), 0)

    def test_mock_payment_success(self):
        payment = Payment.objects.create(
            order=self.order,
            payment_method=Payment.PaymentMethod.MOCK,
            amount=self.order.total_amount,
            currency="INR"
        )

        response = self.client.post(
            f"/api/payments/{payment.id}/process/",
            {"outcome": "success"},
            format="json"
        )

        payment.refresh_from_db()
        self.order.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(payment.status, Payment.PaymentStatus.SUCCESSFUL)
        self.assertTrue(payment.gateway_payment_id.startswith("MOCK_"))
        self.assertEqual(self.order.status, Order.Status.CONFIRMED)

    def test_mock_payment_failure(self):
        payment = Payment.objects.create(
            order=self.order,
            payment_method=Payment.PaymentMethod.MOCK,
            amount=self.order.total_amount,
            currency="INR"
        )

        response = self.client.post(
            f"/api/payments/{payment.id}/process/",
            {"outcome": "failure"},
            format="json"
        )

        payment.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(payment.status, Payment.PaymentStatus.FAILED)
        self.assertTrue(payment.gateway_payment_id.startswith("MOCK_"))
        self.assertNotEqual(payment.failure_reason, "")

    def test_payment_cannot_be_processed_twice(self):
        payment = Payment.objects.create(
            order=self.order,
            payment_method=Payment.PaymentMethod.MOCK,
            amount=self.order.total_amount,
            currency="INR"
        )

        url = f"/api/payments/{payment.id}/process/"

        first_response = self.client.post(
            url,
            {"outcome": "success"},
            format="json"
        )

        second_response = self.client.post(
            url,
            {"outcome": "success"},
            format="json"
        )

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            second_response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_customer_cannot_process_another_users_payment(self):
        another_user = User.objects.create_user(
            username="paymentowner",
            password="TestPassword123!"
        )

        another_order = Order.objects.create(
            user=another_user,
            total_amount=Decimal("500.00"),
            shipping_address="Another Street",
            shipping_city="Bangalore",
            shipping_state="Karnataka",
            shipping_postal_code="560002",
            shipping_phone="9876543211"
        )

        payment = Payment.objects.create(
            order=another_order,
            payment_method=Payment.PaymentMethod.MOCK,
            amount=another_order.total_amount,
            currency="INR"
        )

        response = self.client.post(
            f"/api/payments/{payment.id}/process/",
            {"outcome": "success"},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        payment.refresh_from_db()

        self.assertEqual(payment.status, Payment.PaymentStatus.PENDING)
    

    def test_failed_payment_restores_product_stock(self):
        product = Product.objects.create(
            name="Test Laptop",
            description="Test product",
            price=Decimal("1500.00"),
            stock=7,
            is_active=True
        )

        order_item = OrderItem.objects.create(
            order=self.order,
            product=product,
            product_name=product.name,
            price=product.price,
            quantity=3
        )

        # Simulate stock already deducted during order creation.
        product.stock -= order_item.quantity
        product.save(update_fields=["stock", "updated_at"])

        payment = Payment.objects.create(
            order=self.order,
            payment_method=Payment.PaymentMethod.MOCK,
            amount=self.order.total_amount,
            currency="INR"
        )

        response = self.client.post(
            f"/api/payments/{payment.id}/process/",
            {"outcome": "failure"},
            format="json"
        )

        product.refresh_from_db()
        payment.refresh_from_db()
        self.order.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(product.stock, 7)
        self.assertEqual(payment.status, Payment.PaymentStatus.FAILED)
        self.assertEqual(self.order.status, Order.Status.CANCELLED)

    def test_failed_payment_does_not_restore_stock_twice(self):
        product = Product.objects.create(
            name="Test Phone",
            description="Test product",
            price=Decimal("1500.00"),
            stock=7,
            is_active=True
        )

        order_item = OrderItem.objects.create(
            order=self.order,
            product=product,
            product_name=product.name,
            price=product.price,
            quantity=3
        )

        # Simulate stock deduction during order creation.
        product.stock -= order_item.quantity
        product.save(update_fields=["stock", "updated_at"])

        payment = Payment.objects.create(
            order=self.order,
            payment_method=Payment.PaymentMethod.MOCK,
            amount=self.order.total_amount,
            currency="INR"
        )

        url = f"/api/payments/{payment.id}/process/"

        first_response = self.client.post(
            url,
            {"outcome": "failure"},
            format="json"
        )

        second_response = self.client.post(
            url,
            {"outcome": "failure"},
            format="json"
        )

        product.refresh_from_db()

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            second_response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(product.stock, 7)
