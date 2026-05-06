import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from ..serializers import SignupSerializer, LoginSerializer
from ..models import EmailVerificationToken
from django.core.mail import send_mail
from django.conf import settings

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
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            if User.objects.filter(username=username).exists():
                logger.warning(f"Signup failed: Username '{username}' already exists")
                return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)
            if User.objects.filter(email=email).exists():
                logger.warning(f"Signup failed: Email '{email}' already exists")
                return Response({"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)
                
            user = User.objects.create_user(username=username, email=email, password=password)
            user.is_active = False
            user.save()
            
            token_obj = EmailVerificationToken.objects.create(user=user)
            
            try:
                send_mail(
                    subject='Your Verification Code - SecureMorse',
                    message=f'Your verification code is: {token_obj.otp}\n\nPlease enter this code to verify your email address.',
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception as e:
                logger.error(f"Failed to send email to {email}: {e}")
                # We could delete the user or handle the error, but for now we proceed
            
            logger.info(f"User '{username}' created successfully, pending email verification with OTP.")
            return Response({
                "message": "Verification code sent to your email.",
                "email": email
            }, status=status.HTTP_201_CREATED)
        logger.warning(f"Signup validation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')
        
        if not email or not otp:
            return Response({"error": "Email and OTP are required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            token_obj = EmailVerificationToken.objects.get(user__email=email, otp=otp)
            user = token_obj.user
            
            if user.is_active:
                return Response({"message": "Email is already verified"}, status=status.HTTP_400_BAD_REQUEST)
                
            user.is_active = True
            user.save()
            
            # Delete the token after use
            token_obj.delete()
            
            # Auto-login the user by generating JWT tokens
            refresh = RefreshToken.for_user(user)
            
            logger.info(f"Email verified successfully for user '{user.username}'")
            return Response({
                "message": "Email verified successfully",
                "username": user.username,
                "refresh": str(refresh),
                "access": str(refresh.access_token)
            }, status=status.HTTP_200_OK)
            
        except EmailVerificationToken.DoesNotExist:
            return Response({"error": "Invalid or expired verification code"}, status=status.HTTP_400_BAD_REQUEST)

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
            
            # Check if user exists but is inactive (email not verified)
            user_obj = User.objects.filter(username=username).first()
            if user_obj and not user_obj.is_active and user_obj.check_password(serializer.validated_data['password']):
                logger.warning(f"Login failed for user '{username}': Email not verified")
                return Response({"error": "Please verify your email address to log in. Check your inbox."}, status=status.HTTP_403_FORBIDDEN)
                
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

class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logger.info("Received Google login request")
        token = request.data.get('token')
        
        if not token:
            return Response({"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Verify the Google token
            CLIENT_ID = '716710258281-fnunm6e8detuanu1tqhv9lt24p7pfv9p.apps.googleusercontent.com'
            idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), CLIENT_ID)
            
            # Extract email and name
            email = idinfo.get('email')
            name = idinfo.get('name', '')
            
            if not email:
                return Response({"error": "Email not found in Google token"}, status=status.HTTP_400_BAD_REQUEST)

            # Create user if not exists
            user = User.objects.filter(email=email).first()
            
            if not user:
                if User.objects.filter(username=email).exists():
                    user = User.objects.get(username=email)
                else:
                    user = User.objects.create_user(
                        username=email,
                        email=email,
                        password=None,
                        first_name=name.split()[0] if name else '',
                        last_name=' '.join(name.split()[1:]) if name else ''
                    )
                    logger.info(f"New user '{user.username}' created via Google signup")
            
            # Return JWT tokens
            refresh = RefreshToken.for_user(user)
            logger.info(f"User '{user.username}' logged in via Google successfully")
            
            return Response({
                "success": "Logged in successfully",
                "username": user.username,
                "refresh": str(refresh),
                "access": str(refresh.access_token)
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            logger.warning(f"Invalid Google token provided: {e}")
            return Response({"error": "Invalid Google token"}, status=status.HTTP_400_BAD_REQUEST)
