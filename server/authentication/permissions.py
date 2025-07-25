from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    """
    Permission class to allow only admin users to access the view.
    """
    message = "Only admin users are allowed to perform this action."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission class to allow only the owner of an object or an admin to access it.
    
    This permission requires the object to have a 'user' attribute that can be
    compared with the request's user.
    """
    message = "You do not have permission to perform this action."
    
    def has_object_permission(self, request, view, obj):
        # Allow admins to access any object
        if request.user.is_staff:
            return True
            
        # Check if the object has a user attribute and if it matches the request user
        if hasattr(obj, 'user'):
            return obj.user == request.user
            
        return False


class IsAuthenticatedAndVerified(permissions.IsAuthenticated):
    """
    Permission class to allow only authenticated and verified users to access the view.
    """
    message = "Your account is not verified. Please verify your email address."
    
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        return is_authenticated and request.user.is_active


class ReadOnly(permissions.BasePermission):
    """
    Permission class to allow read-only access to any authenticated user.
    """
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS

