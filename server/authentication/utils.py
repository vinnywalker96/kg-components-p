from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Custom exception handler for the API.
    
    This handler provides more detailed error responses and logs exceptions
    for debugging and monitoring.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Log the exception
    logger.error(f"Exception: {exc} in {context['view'].__class__.__name__}")
    
    # If response is already handled by DRF, customize it
    if response is not None:
        # Extract the original error detail
        error_detail = response.data
        
        # Create a standardized error response
        response.data = {
            'error': True,
            'message': str(exc),
            'details': error_detail
        }
        
        return response
    
    # Handle exceptions not caught by DRF
    if isinstance(exc, Http404):
        return Response({
            'error': True,
            'message': _('Resource not found'),
            'details': str(exc)
        }, status=status.HTTP_404_NOT_FOUND)
    
    elif isinstance(exc, PermissionDenied):
        return Response({
            'error': True,
            'message': _('Permission denied'),
            'details': str(exc)
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Handle any other exceptions
    return Response({
        'error': True,
        'message': _('An unexpected error occurred'),
        'details': str(exc)
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

