from django.urls import path
from .views import (
    ProductListView,
    ProductDetailView,
    ProductCreateView,
    ProductUpdateView,
    ProductDeleteView,
    OrderListView,
    OrderDetailView,
    OrderCreateView,
    OrderUpdateView,
    SaleListView,
    sales_analytics,
    product_analytics
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
    
    # Sale endpoints
    path('sales/', SaleListView.as_view(), name='sale-list'),
    
    # Analytics endpoints
    path('analytics/sales/', sales_analytics, name='sales-analytics'),
    path('analytics/products/', product_analytics, name='product-analytics'),
]

