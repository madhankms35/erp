
from django.db import models
from production.models import MaterialPurchaseRequest


class Supplier(models.Model):
    name = models.CharField(max_length=150)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ("Ordered", "Ordered"),
        ("Partially Received", "Partially Received"),
        ("Received", "Received"),
        ("Cancelled", "Cancelled"),
    ]

    purchase_request = models.OneToOneField(
        MaterialPurchaseRequest,
        on_delete=models.PROTECT,
        related_name="supplier_order",
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name="purchase_orders",
    )
    order_date = models.DateField()
    expected_delivery_date = models.DateField(
        null=True,
        blank=True,
    )
    quantity_ordered = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    status = models.CharField(
        max_length=25,
        choices=STATUS_CHOICES,
        default="Ordered",
    )
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_amount(self):
        return self.quantity_ordered * self.unit_price

    def __str__(self):
        return f"PO #{self.id}"
