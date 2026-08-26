from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


class AuthenticationTests(APITestCase):

    def setUp(self):
        self.register_url = reverse("register")
        self.login_url = reverse("login")
        self.me_url = reverse("me")
        self.logout_url = reverse("logout")
        self.refresh_url = reverse("token-refresh")

        self.user_data = {
            "name": "Test Customer",
            "email": "customer@example.com",
            "password": "password@123",
            "password_confirm": "password@123",
            "role": "customer",
        }

    def create_user(self):
        return User.objects.create_user(
            name="Test Customer",
            email="customer@example.com",
            password="password@123",
            role="customer",
        )

    def login_user(self):
        response = self.client.post(
            self.login_url,
            {
                "email": "customer@example.com",
                "password": "password@123",
            },
            format="json",
        )

        return response

    # ---------------------------------------------------------
    # Registration tests
    # ---------------------------------------------------------

    def test_user_can_register(self):
        response = self.client.post(
            self.register_url,
            self.user_data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            User.objects.count(),
            1,
        )

        self.assertEqual(
            response.data["user"]["email"],
            "customer@example.com",
        )

        self.assertEqual(
            response.data["user"]["role"],
            "customer",
        )

    def test_duplicate_email_is_rejected(self):
        self.create_user()

        response = self.client.post(
            self.register_url,
            self.user_data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_passwords_must_match(self):
        data = self.user_data.copy()
        data["password_confirm"] = "differentpassword"

        response = self.client.post(
            self.register_url,
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_short_password_is_rejected(self):
        data = self.user_data.copy()
        data["password"] = "1234567"
        data["password_confirm"] = "1234567"

        response = self.client.post(
            self.register_url,
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    # ---------------------------------------------------------
    # Login tests
    # ---------------------------------------------------------

    def test_user_can_login(self):
        self.create_user()

        response = self.login_user()

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("user", response.data)

    def test_wrong_password_is_rejected(self):
        self.create_user()

        response = self.client.post(
            self.login_url,
            {
                "email": "customer@example.com",
                "password": "wrongpassword",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    # ---------------------------------------------------------
    # /me/ tests
    # ---------------------------------------------------------

    def test_me_requires_authentication(self):
        response = self.client.get(self.me_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_authenticated_user_can_access_me(self):
        self.create_user()

        login_response = self.login_user()

        access_token = login_response.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.get(self.me_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["email"],
            "customer@example.com",
        )

        self.assertEqual(
            response.data["role"],
            "customer",
        )

    # ---------------------------------------------------------
    # Role tests
    # ---------------------------------------------------------

    def test_customer_has_customer_role(self):
        user = self.create_user()

        self.assertEqual(
            user.role,
            "customer",
        )

    def test_caterer_can_be_created(self):
        caterer = User.objects.create_user(
            name="Test Caterer",
            email="caterer@example.com",
            password="password@123",
            role="caterer",
        )

        self.assertEqual(
            caterer.role,
            "caterer",
        )

    # ---------------------------------------------------------
    # Logout tests
    # ---------------------------------------------------------

    def test_user_can_logout(self):
        self.create_user()

        login_response = self.login_user()

        access_token = login_response.data["access"]
        refresh_token = login_response.data["refresh"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.post(
            self.logout_url,
            {
                "refresh": refresh_token,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_blacklisted_refresh_token_cannot_be_used(self):
        self.create_user()

        login_response = self.login_user()

        access_token = login_response.data["access"]
        refresh_token = login_response.data["refresh"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        logout_response = self.client.post(
            self.logout_url,
            {
                "refresh": refresh_token,
            },
            format="json",
        )

        self.assertEqual(
            logout_response.status_code,
            status.HTTP_200_OK,
        )

        self.client.credentials()

        refresh_response = self.client.post(
            self.refresh_url,
            {
                "refresh": refresh_token,
            },
            format="json",
        )

        self.assertEqual(
            refresh_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
