
from django.db import models


class FinishedGoods(models.Model):
    production_plan = models.OneToOneField(
        'production.ProductionPlan',
        on_delete=models.PROTECT,
        related_name='finished_goods'
    )

    product_name = models.CharField(max_length=100)
    quantity_produced = models.PositiveIntegerField()
    received_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.product_name} - {self.quantity_produced} units"


class Dispatch(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Dispatched', 'Dispatched'),
        ('Cancelled', 'Cancelled'),
    ]

    finished_goods = models.ForeignKey(
        FinishedGoods,
        on_delete=models.PROTECT,
        related_name='dispatches'
    )

    buyer_name = models.CharField(max_length=150)
    invoice_number = models.CharField(max_length=50, blank=True)
    quantity = models.PositiveIntegerField()
    dispatch_date = models.DateField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Dispatch #{self.id} - {self.buyer_name}"
