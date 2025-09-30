# asistente/users/api/urls.py

from django.urls import path
from asistente.users.api.views import UserRegistrationView, UserProfileView

app_name = "users-api"

urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="register"),
    path("me/", UserProfileView.as_view(), name="me"),
]
