from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import AuthStatusView, SignupView, LoginView, LogoutView, GoogleLoginView, VerifyEmailView, EncodeView, DecodeView, api_root, DeleteAccountView, ForgotPasswordView, ResetPasswordView
from .views.api import register_audio_stego, verify_audio_stego

urlpatterns = [

    path('', api_root, name='api-root'),
    path('auth/status/', AuthStatusView.as_view(), name='auth-status'),
    path('auth/signup/', SignupView.as_view(), name='auth-signup'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/google/', GoogleLoginView.as_view(), name='auth-google'),
    path('auth/verify-email/', VerifyEmailView.as_view(), name='auth-verify-email'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/delete-account/', DeleteAccountView.as_view(), name='auth-delete-account'),
    path('auth/forgot-password/', ForgotPasswordView.as_view(), name='auth-forgot-password'),
    path('auth/reset-password/', ResetPasswordView.as_view(), name='auth-reset-password'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/encode/', EncodeView.as_view(), name='api-encode'),
    path('api/decode/', DecodeView.as_view(), name='api-decode'),
    path('api/audio-stego/register/', register_audio_stego, name='api-audio-stego-register'),
    path('api/audio-stego/verify/', verify_audio_stego, name='api-audio-stego-verify'),
]
