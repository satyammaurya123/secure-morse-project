from rest_framework import serializers

class SignupSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)

class EncodeRequestSerializer(serializers.Serializer):
    secret_key = serializers.CharField(required=True, help_text="Password/Key for encryption")
    method = serializers.ChoiceField(choices=[('LSB', 'LSB'), ('DCT', 'DCT')], default='LSB')
    compress = serializers.BooleanField(default=False)
    secret_type = serializers.CharField(required=False, default='text')
    # Fields can be optional here, validated strictly in view
    message = serializers.CharField(required=False, allow_blank=True)
    secret_text = serializers.CharField(required=False, allow_blank=True)
    image = serializers.FileField(required=False)
    cover_media = serializers.FileField(required=False)
    secret_file = serializers.FileField(required=False)

class DecodeRequestSerializer(serializers.Serializer):
    secret_key = serializers.CharField(required=True)
    method = serializers.ChoiceField(choices=[('LSB', 'LSB'), ('DCT', 'DCT')], default='LSB')
    image = serializers.FileField(required=False)
    cover_media = serializers.FileField(required=False)
