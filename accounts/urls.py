from django.urls import path
from .views import UserRegistrationView, CurrentUserView

from rest_framework_simplejwt.views import ( TokenObtainPairView, TokenRefreshView )


urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="user-register"),

    #User login
    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),

    # Refresh access token
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    path("me/", CurrentUserView.as_view(), name="current-user"),
]