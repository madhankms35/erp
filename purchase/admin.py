from django.contrib import admin
from .models import Supplier, PurchaseOrder

admin.site.register(Supplier)
admin.site.register(PurchaseOrder)  