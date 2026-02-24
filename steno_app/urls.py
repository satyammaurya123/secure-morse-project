from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import AuthStatusView, SignupView, LoginView, LogoutView, EncodeView, DecodeView, api_root

urlpatterns = [
    path('', api_root, name='api-root'),
    path('auth/status/', AuthStatusView.as_view(), name='auth-status'),
    path('auth/signup/', SignupView.as_view(), name='auth-signup'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/encode/', EncodeView.as_view(), name='api-encode'),
    path('api/decode/', DecodeView.as_view(), name='api-decode'),
]
