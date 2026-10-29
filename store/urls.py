from django.urls import path

from .views import (
    CartView, CategoryProductListView, ProductDetailView, ProductListView,
)

app_name = "store"

urlpatterns = [
    path("", ProductListView.as_view(), name="product_list"),
    path("category/<slug:slug>/", CategoryProductListView.as_view(),
         name="category_products"),
    path("cart/", CartView.as_view(), name="cart_detail"),
    path("<slug:slug>/", ProductDetailView.as_view(), name="product_detail"),
]
