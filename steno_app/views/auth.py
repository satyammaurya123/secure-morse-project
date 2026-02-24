import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

from ..serializers import SignupSerializer, LoginSerializer

logger = logging.getLogger(__name__)

class AuthStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        logger.debug(f"Auth status check: authenticated as {request.user.username}")
        return Response({"authenticated": True, "username": request.user.username})

class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logger.info("Received signup request")
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            if User.objects.filter(username=username).exists():
                logger.warning(f"Signup failed: Username '{username}' already exists")
                return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)
            user = User.objects.create_user(username=username, password=password)
            refresh = RefreshToken.for_user(user)
            logger.info(f"User '{username}' created successfully")
            return Response({
                "success": "User created successfully",
                "username": username,
                "refresh": str(refresh),
                "access": str(refresh.access_token)
            }, status=status.HTTP_201_CREATED)
        logger.warning(f"Signup validation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logger.info("Received login request")
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            user = authenticate(username=username, password=serializer.validated_data['password'])
            if user:
                refresh = RefreshToken.for_user(user)
                logger.info(f"User '{username}' logged in successfully")
                return Response({
                    "success": "Logged in successfully",
                    "username": user.username,
                    "refresh": str(refresh),
                    "access": str(refresh.access_token)
                })
            logger.warning(f"Login failed for user '{username}': Invalid credentials")
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        logger.warning(f"Login validation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        # With stateless JWTs, logout is primarily a frontend action (deleting tokens).
        # Alternatively, we could blacklist the refresh token here.
        logger.info("User requested logout")
        return Response({"success": "Logged out successfully"})
