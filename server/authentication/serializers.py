from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'password', 'password_confirm']
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True}
        }
    
    def validate(self, attrs):
        # Validate that passwords match
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": _("Password fields didn't match.")})
        
        # Validate password strength
        try:
            validate_password(attrs['password'])
        except ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
            
        # Validate email uniqueness
        email = attrs.get('email', '')
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": _("A user with this email already exists.")})
            
        return attrs
    
    def create(self, validated_data):
        # Remove password_confirm from the data
        validated_data.pop('password_confirm', None)
        
        # Create the user
        user = User.objects.create_user(
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone_number=validated_data.get('phone_number', None),
            password=validated_data['password']
        )
        
        return user


class AdminRegistrationSerializer(UserRegistrationSerializer):
    """
    Serializer for admin registration.
    """
    
    def create(self, validated_data):
        # Remove password_confirm from the data
        validated_data.pop('password_confirm', None)
        
        # Create the admin user
        user = User.objects.create_superuser(
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone_number=validated_data.get('phone_number', None),
            password=validated_data['password']
        )
        
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer that adds additional claims to the token.
    """
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['email'] = user.email
        token['is_staff'] = user.is_staff
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        
        return token
    
    def validate(self, attrs):
        # Get the credentials from the request
        email = attrs.get('email', '')
        password = attrs.get('password', '')
        
        # Authenticate the user
        user = User.objects.filter(email=email).first()
        
        if not user:
            raise AuthenticationFailed(_('No user found with this email address.'))
            
        if not user.check_password(password):
            raise AuthenticationFailed(_('Incorrect password.'))
            
        if not user.is_active:
            raise AuthenticationFailed(_('Account is not active. Please verify your email.'))
            
        # Get the token
        data = super().validate(attrs)
        
        # Add extra responses
        data['user_id'] = str(user.id)
        data['email'] = user.email
        data['is_staff'] = user.is_staff
        data['first_name'] = user.first_name
        data['last_name'] = user.last_name
        
        return data


class AdminTokenObtainPairSerializer(CustomTokenObtainPairSerializer):
    """
    Token serializer specifically for admin users.
    """
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Check if the user is an admin
        if not self.user.is_staff:
            raise AuthenticationFailed(_('User is not authorized to access admin resources.'))
            
        return data


class TokenRefreshSerializer(serializers.Serializer):
    """
    Serializer for refreshing an access token.
    """
    refresh = serializers.CharField()
    
    def validate(self, attrs):
        refresh = attrs.get('refresh')
        
        try:
            token = RefreshToken(refresh)
            access_token = str(token.access_token)
            
            return {
                'access': access_token,
                'refresh': str(token)
            }
        except Exception as e:
            raise serializers.ValidationError(_('Invalid or expired token.'))


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting a password reset.
    """
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        # Check if a user with this email exists
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError(_('No user found with this email address.'))
            
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming a password reset.
    """
    token = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    def validate(self, attrs):
        # Validate that passwords match
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": _("Password fields didn't match.")})
        
        # Validate password strength
        try:
            validate_password(attrs['password'])
        except ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
            
        return attrs


class EmailVerificationSerializer(serializers.Serializer):
    """
    Serializer for email verification.
    """
    token = serializers.CharField(required=True)
    
    def validate_token(self, value):
        # Token validation will be handled in the view
        return value

