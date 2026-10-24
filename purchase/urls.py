
from django.urls import path
from . import views

app_name = "purchase"

urlpatterns = [
    path("", views.purchase_requests, name="purchase_requests"),
    path(
        "create-order/<int:request_id>/",
        views.create_order,
        name="create_order",
    ),
]
