from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase


class AuthFlowTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tester",
            password="admin123",
            real_name="测试用户",
        )

    def test_login_me_and_refresh(self):
        login = self.client.post("/api/v1/auth/login/", {"username": "tester", "password": "admin123"}, format="json")
        self.assertEqual(login.status_code, 200)
        access = login.data["data"]["access"]
        refresh = login.data["data"]["refresh"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        me = self.client.get("/api/v1/auth/me/")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.data["data"]["username"], "tester")

        refreshed = self.client.post("/api/v1/auth/token/refresh/", {"refresh": refresh}, format="json")
        self.assertEqual(refreshed.status_code, 200)
        self.assertIn("access", refreshed.data)
