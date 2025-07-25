from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Define the schema view for Swagger UI
schema_view = get_schema_view(
    openapi.Info(
        title="KG Components API Documentation",
        default_version="v1",
        description=(
            "Welcome to the KG Components API documentation! This API provides endpoints for "
            "user authentication, product management, order processing, and more."
        ),
        terms_of_service="https://www.kgcomponents.com/terms/",
        contact=openapi.Contact(email="support@kgcomponents.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin panel
    path("admin/", admin.site.urls),
    
    # API documentation
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    re_path(r"^swagger(?P<format>\.json|\.yaml)$", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    
    # API endpoints
    path("api/auth/", include("authentication.urls")),
    path("api/users/", include("users.urls")),
    path("api/shop/", include("shop.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

