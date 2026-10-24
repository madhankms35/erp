
from django import forms
from .models import MaterialReceipt
from purchase.models import PurchaseOrder


class MaterialReceiptForm(forms.ModelForm):

    purchase_order = forms.ModelChoiceField(
        queryset=PurchaseOrder.objects.filter(
            status__in=["Ordered", "Partially Received"]
        ).select_related(
            "supplier",
            "purchase_request",
        ).order_by("id"),
        empty_label="Select an open Purchase Order",
        label="Purchase Order",
        widget=forms.Select(attrs={
            "class": "form-select",
        }),
    )

    class Meta:
        model = MaterialReceipt

        fields = [
            "purchase_order",
            "category",
            "inward_date",
            "invoice_number",
            "lot_number",
            "quantity",
            "unit",
            "remarks",
            "received_by",
        ]

        widgets = {
            "category": forms.Select(attrs={
                "class": "form-select",
            }),
            "inward_date": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control",
            }),
            "invoice_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter supplier invoice number",
            }),
            "lot_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter batch or lot number",
            }),
            "quantity": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0.01",
                "placeholder": "Enter received quantity",
            }),
            "unit": forms.Select(attrs={
                "class": "form-select",
            }),
            "remarks": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Optional notes about the delivery",
            }),
            "received_by": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter receiver's name",
            }),
        }

    def clean_quantity(self):
        quantity = self.cleaned_data.get("quantity")

        if quantity is not None and quantity <= 0:
            raise forms.ValidationError(
                "Received quantity must be greater than zero."
            )

        return quantity
