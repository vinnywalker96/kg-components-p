from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Custom exception handler for REST framework.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # If response is None, there was an unhandled exception
    if response is None:
        logger.error(f"Unhandled exception: {str(exc)}")
        return Response(
            {"error": _("An unexpected error occurred.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Add more context to the error response
    if response.status_code == status.HTTP_401_UNAUTHORIZED:
        response.data = {
            "error": _("Authentication credentials were not provided or are invalid."),
            "detail": response.data.get("detail", _("Authentication failed."))
        }
    
    elif response.status_code == status.HTTP_403_FORBIDDEN:
        response.data = {
            "error": _("You do not have permission to perform this action."),
            "detail": response.data.get("detail", _("Permission denied."))
        }
    
    elif response.status_code == status.HTTP_404_NOT_FOUND:
        response.data = {
            "error": _("The requested resource was not found."),
            "detail": response.data.get("detail", _("Not found."))
        }
    
    elif response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
        response.data = {
            "error": _("The method is not allowed for the requested URL."),
            "detail": response.data.get("detail", _("Method not allowed."))
        }
    
    elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        response.data = {
            "error": _("Too many requests. Please try again later."),
            "detail": response.data.get("detail", _("Request limit exceeded."))
        }
    
    # Log the error
    logger.error(f"API Error: {response.status_code} - {response.data}")
    
    return response

