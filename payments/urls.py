from django.urls import path

from .views import PaymentCreateView, PaymentProcessView

urlpatterns = [
    path("", PaymentCreateView.as_view(), name="payment-create"),
    path(
        "<int:pk>/process/",
        PaymentProcessView.as_view(),
        name="payment-process"
    ),
]