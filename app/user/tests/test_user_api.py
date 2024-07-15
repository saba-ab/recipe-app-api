"""
Tests for user api
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token")
ME_URL = reverse("user:me")


def create_user(**params):
    """ Create and return new user"""
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """ Test the public features of api """

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """ Test creating user is successful. """
        payload = {
            "email": "test@example.com",
            "password": "testpass123",
            "name": "Test Name"
        }

        result = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(result.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(email=payload["email"])

        self.assertTrue(user.check_password(payload["password"]))

        self.assertNotIn("password", result.data)

    def test_user_with_email_exists_error(self):
        """ Test error returned if user with email exists"""
        payload = {
            "email": "test@example.com",
            "password": "testpass123",
            "name": "Test Name"
        }
        create_user(**payload)

        result = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """ Test that password must be more than 5 characters """
        payload = {
            "email": "test@example.com",
            "password": "tw",
            "name": "Test Name"
        }
        result = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload["email"]
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """ Test that token is created for the user """
        user_details = {
            "email": "test@example.com",
            "password": "testpass123",
            "name": "Test Name"
        }
        create_user(**user_details)
        payload = {
            "email": user_details["email"],
            "password": user_details["password"]
        }

        result = self.client.post(TOKEN_URL, payload)

        self.assertIn("token", result.data)

        self.assertEqual(result.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        """ Test that token is not created for invalid credentials """
        create_user(email="test@example.com", password="testpass123")
        payload = {
            "email": "test@example.com",
            "password": "wrong"
        }

        result = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("token", result.data)

        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """ Test that token is not created for blank password """
        payload = {
            "email": "test@example.com",
            "password": ""
        }
        result = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("token", result.data)

        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """ Test that authentication is required for users """

        result = self.client.get(ME_URL)

        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """ Test api requests that require authentication """

    def setUp(self):
        self.user = create_user(
            email="test@example.com",
            password="testpass123",
            name="Test Name"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """ Test retrieving profile for logged in user """

        result = self.client.get(ME_URL)

        self.assertEqual(result.status_code, status.HTTP_200_OK)

        self.assertEqual(result.data, {
            "name": self.user.name,
            "email": self.user.email
        })

    def test_post_me_not_allowed(self):
        """ Test that post is not allowed on me url """
        result = self.client.post(ME_URL, {})
        self.assertEqual(result.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """ Test updating the user profile for authenticated user """
        payload = {
            "name": "New Name",
            "password": "newpassword123"
        }
        result = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload["name"])
        self.assertTrue(self.user.check_password(payload["password"]))
        self.assertEqual(result.status_code, status.HTTP_200_OK)
