from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rsa_private_key = models.TextField(blank=True, null=True)
    rsa_public_key = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

class AudioStegoLog(models.Model):
    uploader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audio_stego_logs')
    image_hash = models.CharField(max_length=64, unique=True, help_text="SHA-256 Hash of the generated stego image")
    version = models.IntegerField(default=1, help_text="Steganography protocol version")
    created_at = models.DateTimeField(auto_now_add=True)
    extraction_attempts = models.IntegerField(default=0)

    def __str__(self):
        return f"AudioStegoLog {self.image_hash[:8]} by {self.uploader.username}"

import random
import string

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

class EmailVerificationToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_verification_token')
    otp = models.CharField(max_length=6, default=generate_otp)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OTP for {self.user.username}"

class PasswordResetToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='password_reset_token')
    otp = models.CharField(max_length=6, default=generate_otp)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Password Reset OTP for {self.user.username}"
