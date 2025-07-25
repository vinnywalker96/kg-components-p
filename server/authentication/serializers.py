from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from phonenumber_field.serializerfields import PhoneNumberField
import re

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['email', 'password', 'password_confirm', 'first_name', 'last_name', 'phone_number']
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True}
        }
    
    def validate(self, attrs):
        # Check if passwords match
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": _("Password fields didn't match.")})
        
        # Validate email format
        email = attrs['email']
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            raise serializers.ValidationError({"email": _("Enter a valid email address.")})
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": _("A user with that email already exists.")})
        
        return attrs
    
    def create(self, validated_data):
        # Remove password_confirm from validated data
        validated_data.pop('password_confirm')
        
        # Create user
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone_number=validated_data.get('phone_number')
        )
        
        return user

class UserLoginSerializer(TokenObtainPairSerializer):
    """
    Serializer for user login.
    """
    def validate(self, attrs):
        # Call parent validate method
        data = super().validate(attrs)
        
        # Check if user is active and verified
        user = self.user
        if not user.is_active:
            raise serializers.ValidationError(_("User account is disabled."))
        
        if not user.is_verified:
            raise serializers.ValidationError(_("Email not verified. Please check your email for verification link."))
        
        # Add user data to response
        data.update({
            'user_id': str(user.id),
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_admin': user.is_staff
        })
        
        return data

class AdminLoginSerializer(TokenObtainPairSerializer):
    """
    Serializer for admin login.
    """
    def validate(self, attrs):
        # Call parent validate method
        data = super().validate(attrs)
        
        # Check if user is admin
        user = self.user
        if not user.is_staff:
            raise serializers.ValidationError(_("You do not have permission to access the admin panel."))
        
        # Add user data to response
        data.update({
            'user_id': str(user.id),
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_admin': user.is_staff
        })
        
        return data

class EmailVerificationSerializer(serializers.Serializer):
    """
    Serializer for email verification.
    """
    token = serializers.CharField(required=True)

class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for password reset request.
    """
    email = serializers.EmailField(required=True)

class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation.
    """
    token = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    def validate(self, attrs):
        # Check if passwords match
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": _("Password fields didn't match.")})
        
        return attrs

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile.
    """
    phone_number = PhoneNumberField(required=False)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone_number', 'physical_address', 'profile_picture']
        read_only_fields = ['id', 'email']

