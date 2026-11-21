
from types import SimpleNamespace

from django.contrib.auth.models import User
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserProfile
from .permissions import IsCustomer, IsSeller, IsAdmin


class AuthenticationAPITests(APITestCase):

    def setUp(self):
        # API URLs
        self.register_url = reverse("user-register")
        self.login_url = reverse("token_obtain_pair")
        self.refresh_url = reverse("token_refresh")
        self.me_url = reverse("current-user")

        # Create test user
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPassword@123"
        )

        # Create associated user profile
        self.profile = UserProfile.objects.create(
            user=self.user,
            role=UserProfile.Role.CUSTOMER,
            phone_number="9876543210"
        )

    # -------------------------------
    # User Registration Tests
    # -------------------------------

    def test_user_registration(self):
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "NewPassword@123",
            "phone_number": "9876543211",
            "role": "customer"
        }

        response = self.client.post(
            self.register_url,
            data
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        new_user = User.objects.get(username="newuser")

        self.assertTrue(
            new_user.check_password("NewPassword@123")
        )

        self.assertTrue(
            UserProfile.objects.filter(user=new_user).exists()
        )

    # -------------------------------
    # User Login Tests
    # -------------------------------

    def test_user_login(self):
        data = {
            "username": "testuser",
            "password": "TestPassword@123"
        }

        response = self.client.post(
            self.login_url,
            data
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_user_login_with_invalid_password(self):
        data = {
            "username": "testuser",
            "password": "WrongPassword123"
        }

        response = self.client.post(
            self.login_url,
            data
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    # -------------------------------
    # Current User Tests
    # -------------------------------

    def test_get_current_user(self):
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.get(self.me_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data["username"],
            "testuser"
        )

        self.assertEqual(
            response.data["role"],
            "customer"
        )

    def test_current_user_without_token(self):
        response = self.client.get(self.me_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    # -------------------------------
    # JWT Refresh Token Test
    # -------------------------------

    def test_refresh_token(self):
        refresh = RefreshToken.for_user(self.user)

        response = self.client.post(
            self.refresh_url,
            {"refresh": str(refresh)}
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertIn("access", response.data)

    # -------------------------------
    # Role Permission Tests
    # -------------------------------

    def test_customer_permission(self):
        permission = IsCustomer()

        request = SimpleNamespace(user=self.user)

        self.assertTrue(
            permission.has_permission(request, None)
        )

    def test_seller_permission(self):
        seller = User.objects.create_user(
            username="seller_test",
            password="SellerPassword@123"
        )

        UserProfile.objects.create(
            user=seller,
            role=UserProfile.Role.SELLER
        )

        permission = IsSeller()

        request = SimpleNamespace(user=seller)

        self.assertTrue(
            permission.has_permission(request, None)
        )

    def test_admin_permission(self):
        admin = User.objects.create_user(
            username="admin_test",
            password="AdminPassword@123",
            is_staff=True
        )

        permission = IsAdmin()

        request = SimpleNamespace(user=admin)

        self.assertTrue(
            permission.has_permission(request, None)
        )
