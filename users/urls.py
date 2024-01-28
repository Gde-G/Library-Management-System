from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


from .views import EmailConfirmationView, PasswordsCheckMatchView, PasswordChangeView

urlpatterns = [
    path('users/confirm-email/<uidb64>/<token>/',
         EmailConfirmationView.as_view(), name='account_confirm_email'),
    path("check-password-match/", PasswordsCheckMatchView.as_view(),
         name="check_password_match"),

    path("password-change/", PasswordChangeView.as_view(), name='password-change'),

    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

]
