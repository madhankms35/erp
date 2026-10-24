
from django.urls import path
from . import views

app_name = "qc"

urlpatterns = [
    path("", views.inspection_list, name="inspection_list"),
    path(
        "inspect/<int:receipt_id>/",
        views.update_inspection,
        name="update_inspection",
    ),
]
