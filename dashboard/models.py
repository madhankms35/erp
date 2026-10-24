from django.db import models


class ProductionRequest(models.Model):
    product = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField()
    color = models.CharField(max_length=100)
    color_type = models.CharField(max_length=30)
    sleeve = models.CharField(max_length=20)
    fabric = models.CharField(max_length=50)
    required_date = models.DateField()
    priority = models.CharField(max_length=20)
    remarks = models.TextField(blank=True,null=True)
    status = models.CharField(max_length=30,default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"Production Request #{self.id} - {self.product}"