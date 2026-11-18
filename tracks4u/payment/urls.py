from django.urls import path

from payment.api.views import MyPurchasesView, OrderCreateView, OrderDetailView

urlpatterns = [
    path("orders/", OrderCreateView.as_view(), name="orders"),
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="order-detail"),
    path("my-purchases/", MyPurchasesView.as_view(), name="my-purchases"),
]
