from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # If response is None, there was an unhandled exception
    if response is None:
        logger.error(f"Unhandled exception: {exc}")
        return Response(
            {"error": _("An unexpected error occurred.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Add more context to the response
    if response.status_code == 401:
        response.data = {
            "error": _("Authentication credentials were not provided or are invalid."),
            "details": response.data
        }
    elif response.status_code == 403:
        response.data = {
            "error": _("You do not have permission to perform this action."),
            "details": response.data
        }
    elif response.status_code == 404:
        response.data = {
            "error": _("The requested resource was not found."),
            "details": response.data
        }
    elif response.status_code == 405:
        response.data = {
            "error": _("Method not allowed."),
            "details": response.data
        }
    elif response.status_code == 429:
        response.data = {
            "error": _("Too many requests. Please try again later."),
            "details": response.data
        }
    
    return response

