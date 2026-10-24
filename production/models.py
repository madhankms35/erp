from django.db import models

class ProductionRequest(models.Model):

    PRODUCT_CHOICES = [
        ('Shirt', 'Shirt'),
        ('TShirt', 'T-Shirt'),
        ('PoloTShirt', 'Polo T-Shirt'),
        ('Hoodie', 'Hoodie'),
        ('Trouser', 'Trouser'),
    ]

    COLOR_TYPE_CHOICES = [
        ('Solid', 'Solid'),
        ('Pattern', 'Pattern'),
    ]

    SLEEVE_CHOICES = [
        ('Half Sleeve', 'Half Sleeve'),
        ('Full Sleeve', 'Full Sleeve'),
        ('Sleeveless', 'Sleeveless'),
        ('Three Quarter', 'Three Quarter'),
    ]

    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Urgent', 'Urgent'),
    ]

    product = models.CharField(max_length=50,choices=PRODUCT_CHOICES)
    quantity = models.PositiveIntegerField()
    color = models.CharField(max_length=100)
    color_type = models.CharField(max_length=30,choices=COLOR_TYPE_CHOICES)
    sleeve = models.CharField(max_length=20,choices=SLEEVE_CHOICES)
    fabric = models.CharField(max_length=50)
    required_date = models.DateField()
    priority = models.CharField(max_length=20,choices=PRIORITY_CHOICES)
    remarks = models.TextField(blank=True,null=True)
    status = models.CharField(max_length=30,default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"Production Request #{self.id} - {self.product}"

class ProductMaterial(models.Model):
    product_name = models.CharField(max_length=100,null=False)
    material_name = models.CharField(max_length=100,null=False)
    quantity_per_unit = models.IntegerField(null=False)
    unit = models.CharField(max_length=20, null=False)


class ProductionPlan(models.Model):
    STATUS_CHOICES = [
        ('Allotted', 'Allotted'),
        ('Waiting for Materials', 'Waiting for Materials'),
        ('Waiting for Manpower', 'Waiting for Manpower'),
        ('Waiting for Line', 'Waiting for Line'),
        ('In Production', 'In Production'),
        ('On Hold', 'On Hold'),
        ('Issue', 'Issue'),
        ('Completed', 'Completed'),
    ]

    production_request = models.ForeignKey(
        ProductionRequest,
        on_delete=models.PROTECT,
        related_name='plans'
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='Allotted'
    )
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"Plan #{self.id} - {self.production_request.product}"


class MaterialRequest(models.Model):

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Partially Fulfilled', 'Partially Fulfilled'),
        ('Fulfilled', 'Fulfilled'),
        ('Rejected', 'Rejected'),
    ]

    production_plan = models.ForeignKey(
        ProductionPlan,
        on_delete=models.PROTECT,
        related_name='material_requests'
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Material Request #{self.id} - {self.status}"



class MaterialRequestItem(models.Model):
    material_request = models.ForeignKey(
        MaterialRequest,
        on_delete=models.CASCADE,
        related_name='items'
    )
    material_name = models.CharField(max_length=100)
    quantity_requested = models.DecimalField(
        max_digits=12, decimal_places=2
    )
    unit = models.CharField(max_length=20)

    # Quantity the store has actually issued
    quantity_issued = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # Shortage identified when the request was created
    quantity_short = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    def __str__(self):
        return f"{self.material_name} - {self.quantity_requested} {self.unit}"


class MaterialPurchaseRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Ordered', 'Ordered'),
        ('Received', 'Received'),
        ('Cancelled', 'Cancelled'),
    ]

    production_plan = models.ForeignKey(
        ProductionPlan,
        on_delete=models.PROTECT,
        related_name='purchase_requests'
    )

    material_name = models.CharField(max_length=100)

    quantity_requested = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    unit = models.CharField(max_length=20)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    remarks = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['production_plan', 'material_name'],
                name='unique_plan_material_purchase'
            )
        ]

    def __str__(self):
        return (
            f"Purchase Request #{self.id} - "
            f"{self.material_name}"
        )


