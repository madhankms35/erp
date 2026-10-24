from django import forms
from .models import ProductionRequest


class ProductionForm(forms.ModelForm):
    class Meta:
        model = ProductionRequest

        fields = [
            'product',
            'quantity',
            'color',
            'color_type',
            'sleeve',
            'fabric',
            'required_date',
            'priority',
            'remarks',
        ]

        widgets = {
            'product': forms.Select(attrs={
                'class': 'form-select',
            }),

            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Enter quantity',
            }),

            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter color',
            }),

            'color_type': forms.Select(attrs={
                'class': 'form-select',
            }),

            'sleeve': forms.Select(attrs={
                'class': 'form-select',
            }),

            # 'fabric': forms.Select(attrs={
            #     'class': 'form-select',
            # }),
            'fabric': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'required_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
            }),

            'priority': forms.Select(attrs={
                'class': 'form-select',
            }),

            'remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter additional instructions (optional)',
            }),
        }
