"""
Test for recipe API.
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPES_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    """ Return recipe detail url """
    return reverse("recipe:recipe-detail", args=[recipe_id])


def create_recipe(user, **params):
    """ Create and return sample recipe """
    defaults = {
        "title": "Sample Recipe",
        "time_minutes": 12,
        "price": Decimal("5.25"),
        "description": "sample description",
        "link": "http://example.com/recipe"
    }
    defaults.update(params)
    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


def create_user(**params):
    """ Create and return sample user """
    return get_user_model().objects.create_user(**params)


class PublicRecipeAPITests(TestCase):
    """ Test unauthenticated api requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """ Test that authentication is required """
        result = self.client.get(RECIPES_URL)
        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """ Test authenticated api requests"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email="user@example.com", password="password123")

        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """ Test retrieving a list of recipes """
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        result = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by("-id")

        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """ Test retrieving recipes for user """
        other_user = create_user(
            email="other@example.com",
            password="password123"
        )
        create_recipe(user=other_user)
        create_recipe(user=self.user)

        result = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data, serializer.data)

    def test_get_recipe_detail(self):
        """ Test get recipe detail """

        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        result = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(result.data, serializer.data)

    def test_create_recipe(self):
        """ Test creating a recipe """
        payload = {
            "title": "Chocolate Cake",
            "time_minutes": 30,
            "price": Decimal("10.00")
        }
        result = self.client.post(RECIPES_URL, payload)

        self.assertEqual(result.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=result.data['id'])
        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """ Test updating a recipe with patch """
        original_link = "http://example.com/recipe"
        recipe = create_recipe(
            user=self.user,
            title="sample title",
            link=original_link
        )
        payload = {"link": "http://example.com/updated"}

        url = detail_url(recipe.id)
        result = self.client.patch(url, payload)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertNotEqual(result.data["link"], original_link)
