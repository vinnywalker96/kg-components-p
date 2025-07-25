from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information.
    """
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone_number', 'physical_address', 'profile_picture',
            'is_active', 'is_verified', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'email', 'is_active', 'is_verified', 'date_joined', 'last_login']
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile information.
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'physical_address', 'profile_picture']
    
    def validate_phone_number(self, value):
        """
        Validate the phone number format.
        """
        if value and not value.is_valid():
            raise serializers.ValidationError(_("Invalid phone number format."))
        return value


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for changing user password.
    """
    current_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)
    
    def validate_current_password(self, value):
        """
        Validate that the current password is correct.
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Current password is incorrect."))
        return value
    
    def validate(self, data):
        """
        Validate that the new password and confirm password match and meet password requirements.
        """
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': _("New password and confirm password do not match.")
            })
        
        try:
            validate_password(data['new_password'], self.context['request'].user)
        except ValidationError as e:
            raise serializers.ValidationError({
                'new_password': list(e.messages)
            })
        
        return data
    
    def save(self, **kwargs):
        """
        Save the new password.
        """
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class AdminUserListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing users (admin view).
    """
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'phone_number',
            'is_active', 'is_verified', 'is_staff', 'date_joined'
        ]
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class AdminUserDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed user information (admin view).
    """
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone_number', 'physical_address', 'profile_picture',
            'is_active', 'is_verified', 'is_staff', 'is_superuser',
            'date_joined', 'last_login', 'created_at', 'updated_at'
        ]
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user information (admin view).
    """
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'phone_number',
            'physical_address', 'is_active', 'is_verified', 'is_staff'
        ]
    
    def validate_email(self, value):
        """
        Validate that the email is unique.
        """
        user = self.instance
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError(_("A user with this email already exists."))
        return value

