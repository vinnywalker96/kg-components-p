from django.urls import path
from .views import (
    # Product views
    ProductListView,
    ProductDetailView,
    ProductCreateView,
    ProductUpdateView,
    ProductDeleteView,
    
    # Order views
    OrderListView,
    OrderDetailView,
    OrderCreateView,
    OrderUpdateView,
    
    # Sale views
    SaleListView,
    SaleDetailView,
    
    # Analytics views
    SalesAnalyticsView,
    ProductAnalyticsView
)

app_name = 'shop'

urlpatterns = [
    # Product endpoints
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<uuid:id>/', ProductDetailView.as_view(), name='product-detail'),
    path('products/create/', ProductCreateView.as_view(), name='product-create'),
    path('products/<uuid:id>/update/', ProductUpdateView.as_view(), name='product-update'),
    path('products/<uuid:id>/delete/', ProductDeleteView.as_view(), name='product-delete'),
    
    # Order endpoints
    path('orders/', OrderListView.as_view(), name='order-list'),
    path('orders/<uuid:id>/', OrderDetailView.as_view(), name='order-detail'),
    path('orders/create/', OrderCreateView.as_view(), name='order-create'),
    path('orders/<uuid:id>/update/', OrderUpdateView.as_view(), name='order-update'),
    
    # Sale endpoints (admin only)
    path('sales/', SaleListView.as_view(), name='sale-list'),
    path('sales/<uuid:id>/', SaleDetailView.as_view(), name='sale-detail'),
    
    # Analytics endpoints (admin only)
    path('analytics/sales/', SalesAnalyticsView.as_view(), name='sales-analytics'),
    path('analytics/products/', ProductAnalyticsView.as_view(), name='product-analytics'),
]

