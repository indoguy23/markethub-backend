
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Product


class ProductAPITests(APITestCase):

    def setUp(self):
        self.product = Product.objects.create(
            name="Wireless Headphones",
            description="Bluetooth headphones",
            price=Decimal("1999.00"),
            stock=25,
            image="https://example.com/headphones.jpg",
            is_active=True,
        )

        self.list_url = reverse("product-list")
        self.detail_url = reverse(
            "product-detail",
            args=[self.product.id]
        )

    def test_get_all_products(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_product(self):
        data = {
            "name": "Gaming Mouse",
            "description": "Wireless gaming mouse",
            "price": "1499.00",
            "stock": 15,
            "image": "",
            "is_active": True,
        }

        response = self.client.post(self.list_url, data)

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )
        self.assertEqual(Product.objects.count(), 2)

    def test_get_single_product(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["name"],
            "Wireless Headphones"
        )

    def test_update_product(self):
        data = {
            "name": "Premium Headphones",
            "description": "Updated headphones",
            "price": "2499.00",
            "stock": 30,
            "image": "",
            "is_active": True,
        }

        response = self.client.put(self.detail_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.product.refresh_from_db()

        self.assertEqual(self.product.name, "Premium Headphones")
        self.assertEqual(self.product.price, Decimal("2499.00"))

    def test_partial_update_product(self):
        data = {"price": "2299.00"}

        response = self.client.patch(self.detail_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.product.refresh_from_db()

        self.assertEqual(self.product.price, Decimal("2299.00"))
        self.assertEqual(self.product.stock, 25)

    def test_delete_product(self):
        response = self.client.delete(self.detail_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT
        )
        self.assertEqual(Product.objects.count(), 0)

    def test_create_product_with_invalid_data(self):
        data = {
            "description": "Product without a name",
            "price": "1499.00",
            "stock": 10,
        }

        response = self.client.post(self.list_url, data)

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(Product.objects.count(), 1)
