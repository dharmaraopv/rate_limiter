from httpx import ASGITransport, AsyncClient
import pytest
import unittest
from fastapi.testclient import TestClient
from main import app

sync_client = TestClient(app)


def get_async_client():
    return AsyncClient(transport=ASGITransport(app), base_url="http://test")


class TestRateLimiter(unittest.IsolatedAsyncioTestCase):
    """
    E2E tests for the FastAPI rate limiter API.
    These tests verify the behavior of the API endpoints for configuring the rate limiter
    and checking if a user is rate-limited.
    """

    def test_configure_rate_limiter(self):
        """
        Test the /api/configure endpoint to ensure that the rate limiter is configured correctly.
        Verifies that the configuration is applied and returned as expected.
        """
        # Send a POST request to configure the rate limiter
        response = sync_client.post("/api/configure", json={"interval": 60, "limit": 10})

        # Ensure the request was successful (status code 200)
        self.assertEqual(response.status_code, 200)

        # Ensure the response contains the correct configuration
        self.assertEqual(response.json(), {"interval": 60, "limit": 10})

    @pytest.mark.anyio
    async def test_is_rate_limited_false_response(self):
        """
        Test the /api/is_rate_limited/{unique_token} endpoint.
        Verifies that a user is not rate-limited when they have not exceeded the limit.
        """
        async with get_async_client() as client:
            # Send a GET request to check if the user is rate-limited
            response = await client.get("/api/is_rate_limited/123")

            # Ensure the request was successful (status code 200)
            self.assertEqual(response.status_code, 200)

            # Ensure the user is not rate-limited (response is "false")
            self.assertEqual(response.text, "false")

    @pytest.mark.anyio
    async def test_is_rate_limited_true_response(self):
        """
        Test the /api/is_rate_limited/{unique_token} endpoint.
        First, configure the rate limiter with a limit of 1 request per 10 seconds.
        Then, send two requests and verify that the second request is rate-limited.
        """
        async with get_async_client() as client:
            # Configure the rate limiter with an interval of 10 seconds and a limit of 1 request
            await client.post("/api/configure", json={"interval": 10, "limit": 1})

            # Send the first request (should not be rate-limited)
            await client.get("/api/is_rate_limited/123")

            # Send the second request (should now be rate-limited)
            response = await client.get("/api/is_rate_limited/123")

            # Ensure the request was successful (status code 200)
            self.assertEqual(response.status_code, 200)

            # Ensure the user is now rate-limited (response is "true")
            self.assertEqual(response.text, "true")

    def test_configure_rate_limiter_invalid_interval(self):
        """
        Test that the /api/configure endpoint returns an error for invalid interval values.
        """
        # Invalid interval: negative value
        invalid_payload = {
            "interval": -5,  # Invalid interval (must be >= 1)
            "limit": 100
        }

        # Make a POST request with invalid data
        response = sync_client.post("/api/configure", json=invalid_payload)

        # Ensure that the response status is 422 Unprocessable Entity (validation error)
        self.assertEqual(response.status_code, 422)

        # Check if the correct validation error is raised
        self.assertIn("greater_than_equal", response.json()["detail"][0]["type"])

    def test_configure_rate_limiter_invalid_limit(self):
        """
        Test that the /api/configure endpoint returns an error for invalid limit values.
        """
        # Invalid limit: non-positive value
        invalid_payload = {
            "interval": 60,
            "limit": 0  # Invalid limit (must be >= 1)
        }

        # Make a POST request with invalid data
        response = sync_client.post("/api/configure", json=invalid_payload)

        # Ensure that the response status is 422 Unprocessable Entity (validation error)
        self.assertEqual(response.status_code, 422)

        # Check if the correct validation error is raised
        self.assertIn("greater_than_equal", response.json()["detail"][0]["type"])

    def test_is_rate_limited_invalid_unique_token(self):
        """
        Test that the /api/is_rate_limited/{unique_token} endpoint returns an error for invalid token format.
        """
        # Invalid unique token: exceeds maximum length
        invalid_token = "x" * 101  # Invalid token (more than 100 characters)

        # Make a GET request with an invalid token
        response = sync_client.get(f"/api/is_rate_limited/{invalid_token}")

        # Ensure that the response status is 422 Unprocessable Entity (validation error)
        self.assertEqual(response.status_code, 422)

        # Check if the correct validation error is raised for max_length
        self.assertIn("string_too_long", response.json()["detail"][0]["type"])

    def test_is_rate_limited_empty_unique_token(self):
        """
        Test that the /api/is_rate_limited/{unique_token} endpoint returns an error for empty token.
        """
        # Empty unique token
        invalid_token = ""

        # Make a GET request with an empty token
        response = sync_client.get(f"/api/is_rate_limited/{invalid_token}")

        # Ensure that the response status is 404
        self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
    unittest.main()
