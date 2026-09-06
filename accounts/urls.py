from django.urls import path
from django.contrib.auth import views as auth_views

from .views import (
    register,
    user_login,
    user_logout,
    user_list,
    register_api,
    profile_update,
    password_reset_set_password,
    DevelopmentPasswordResetDoneView,
    DevelopmentPasswordResetView,
)

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [

    # Normal website
    path("register/", register, name="register"),
    path("login/", user_login, name="login"),
    path("logout/", user_logout, name="logout"),
    path("profile/update/", profile_update, name="profile_update"),

    # User APIs
    path("api/users/", user_list, name="user_list"),
    path("api/register/", register_api, name="register_api"),

    # JWT Authentication
    path(
        "api/login/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair"
    ),

    path(
        "api/token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh"
    ),

    # Password Reset
    path(
        "forgot-password/",
        DevelopmentPasswordResetView.as_view(
            template_name="accounts/forgot_password.html",
            email_template_name="accounts/password_reset_email.html"
        ),
        name="password_reset"
    ),

    path(
        "reset-password/done/",
        DevelopmentPasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html"
        ),
        name="password_reset_done"
    ),

    path(
        "reset-password/<uidb64>/set-password/",
        password_reset_set_password,
        name="password_reset_set_password",
    ),

    path(
        "reset-password/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html"
        ),
        name="password_reset_confirm"
    ),

    path(
        "reset-password/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html"
        ),
        name="password_reset_complete"
    ),
]