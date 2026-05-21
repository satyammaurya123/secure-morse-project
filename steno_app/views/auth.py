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
from ..models import EmailVerificationToken, PasswordResetToken
import requests
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
                response = requests.post(
                    settings.GOOGLE_SCRIPT_URL,
                    json={
                        "to": user.email,
                        "subject": "Your Verification Code - SecureMorse",
                        "message": f"Your verification code is: {token_obj.otp}\n\nPlease enter this code to verify your email address."
                    },
                    timeout=10
                )
                response.raise_for_status()
            except Exception as e:
                logger.error(f"Failed to send email to {email}: {e}")
                user.delete()
                return Response({"error": "Failed to send verification email. Please try again or contact support."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
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

class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        password = request.data.get('password')

        # Google-OAuth users have no usable password — skip password check
        if user.has_usable_password():
            if not password:
                return Response(
                    {"error": "Password is required to delete your account."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not user.check_password(password):
                logger.warning(f"Delete account failed for '{user.username}': incorrect password")
                return Response(
                    {"error": "Incorrect password. Account deletion cancelled."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        username = user.username
        user.delete()
        logger.info(f"Account '{username}' permanently deleted.")
        return Response(
            {"message": "Your account has been permanently deleted."},
            status=status.HTTP_200_OK
        )

class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        user = User.objects.filter(email=email).first()
        if not user:
            # For security, we might want to return the same response whether the email exists or not,
            # but to be helpful here we'll let the user know.
            return Response({"error": "No user found with this email"}, status=status.HTTP_404_NOT_FOUND)
            
        if not user.has_usable_password():
            return Response({"error": "This account uses Google Sign-In. Password reset is not available."}, status=status.HTTP_400_BAD_REQUEST)

        # Delete existing token if any
        PasswordResetToken.objects.filter(user=user).delete()
        
        token_obj = PasswordResetToken.objects.create(user=user)
        
        try:
            response = requests.post(
                settings.GOOGLE_SCRIPT_URL,
                json={
                    "to": user.email,
                    "subject": "Password Reset Code - SecureMorse",
                    "message": f"Your password reset code is: {token_obj.otp}\n\nPlease enter this code to reset your password."
                },
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Password reset OTP sent to {email}")
            return Response({"message": "Password reset code sent to your email."}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Failed to send password reset email to {email}: {e}")
            return Response({"error": "Failed to send email. Please try again later."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')
        new_password = request.data.get('new_password')
        
        if not all([email, otp, new_password]):
            return Response({"error": "Email, OTP, and new password are required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            token_obj = PasswordResetToken.objects.get(user__email=email, otp=otp)
            user = token_obj.user
            
            user.set_password(new_password)
            user.save()
            
            token_obj.delete()
            
            logger.info(f"Password reset successfully for user '{user.username}'")
            return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)
            
        except PasswordResetToken.DoesNotExist:
            return Response({"error": "Invalid or expired reset code"}, status=status.HTTP_400_BAD_REQUEST)
