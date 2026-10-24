from django.db import models
from production.models import *

class MaterialReceipt(models.Model):
    CATEGORY_CHOICES = [
        ('Fabric', 'Fabric'),
        ('Yarn', 'Yarn'),
        ('Thread', 'Thread'),
        ('Trims', 'Trims'),
        ('Accessories', 'Accessories'),
        ('Chemicals', 'Chemicals'),
        ('Other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('Pending Inspection', 'Pending Inspection'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
    ]

    UNIT_CHOICES = [
        ('Meter', 'Meter'),
        ('Kg', 'Kg'),
        ('Pieces', 'Pieces'),
        ('Rolls', 'Rolls'),
    ]

    material_name = models.CharField(max_length=100)
    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES
    )

    supplier = models.CharField(max_length=100)
    inward_date = models.DateField()

    invoice_number = models.CharField(max_length=50)
    lot_number = models.CharField(max_length=50)
    
    purchase_order = models.ForeignKey(
    'purchase.PurchaseOrder',
    on_delete=models.PROTECT,
    null=True,
    blank=True,
    related_name='material_receipts')

    purchase_order_number = models.CharField(
    max_length=50,
    blank=True)

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    unit = models.CharField(
        max_length=20,
        choices=UNIT_CHOICES
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='Pending Inspection'
    )

    location = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)

    received_by = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.material_name} - {self.quantity} {self.unit} ({self.status})"


class StoreMaterialIssue(models.Model):
    material_request = models.ForeignKey(
        MaterialRequest,
        on_delete=models.PROTECT,
        related_name="store_issues"
    )
    issued_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"Store Issue #{self.id}"


class StoreMaterialIssueItem(models.Model):
    store_issue = models.ForeignKey(
        StoreMaterialIssue,
        on_delete=models.PROTECT,
        related_name="items"
    )
    material_request_item = models.ForeignKey(
        MaterialRequestItem,
        on_delete=models.PROTECT,
        related_name="store_issue_items"
    )
    quantity_issued = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    unit = models.CharField(max_length=20)

    def __str__(self):
        return (
            f"{self.material_request_item.material_name}"
            f" - {self.quantity_issued} {self.unit}"
        )
    