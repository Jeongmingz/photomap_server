from django.urls import path

from accounts.apis import LoginAPI

urlpatterns = [
	path("oauth-login", LoginAPI.as_view(), name="auth-login")
]
