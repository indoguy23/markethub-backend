
from django.contrib.auth.models import User
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from .models import Category


class CategoryAPITestCase(APITestCase):

    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username="category_test_user",
            password="TestPassword@123"
        )

        # Authenticate API test requests
        self.client.force_authenticate(user=self.user)

        # Create a test category
        self.category = Category.objects.create(
            name="Electronics",
            description="Electronic devices",
            is_active=True
        )

        # API URLs
        self.list_url = reverse("category-list")
        self.detail_url = reverse(
            "category-detail",
            args=[self.category.id]
        )

    def test_get_categories(self):
        response = self.client.get(self.list_url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_create_category(self):
        data = {
            "name": "Clothing",
            "description": "Fashion and apparel",
            "is_active": True
        }

        response = self.client.post(self.list_url, data)

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

    def test_get_category_detail(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_update_category(self):
        data = {
            "name": "Updated Electronics",
            "description": "Updated description",
            "is_active": True
        }

        response = self.client.put(self.detail_url, data)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_partial_update_category(self):
        response = self.client.patch(
            self.detail_url,
            {"name": "Updated Name"}
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_delete_category(self):
        response = self.client.delete(self.detail_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT
        )

    def test_create_category_with_invalid_data(self):
        response = self.client.post(
            self.list_url,
            {"name": ""}
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
