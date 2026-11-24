from django.urls import path

from .views import (
    CartView,
    AddCartItemView,
    CartItemDetailView,
)

urlpatterns = [
    # View customer's cart
    path(
        "",
        CartView.as_view(),
        name="cart-detail"
    ),

    # Add product to cart
    path(
        "items/",
        AddCartItemView.as_view(),
        name="cart-add-item"
    ),

    # Update or remove cart item
    path(
        "items/<int:pk>/",
        CartItemDetailView.as_view(),
        name="cart-item-detail"
    ),
]
