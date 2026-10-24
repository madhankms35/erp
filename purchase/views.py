
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404

from production.models import MaterialPurchaseRequest
from .models import Supplier, PurchaseOrder


def create_order(request, request_id):
    purchase_request = get_object_or_404(
        MaterialPurchaseRequest,
        pk=request_id
    )

    # Prevent creating a duplicate supplier order.
    if PurchaseOrder.objects.filter(
        purchase_request=purchase_request
    ).exists():
        return redirect("purchase:purchase_requests")

    if purchase_request.status != "Pending":
        return redirect("purchase:purchase_requests")

    suppliers = Supplier.objects.filter(is_active=True).order_by("name")
    error = ""

    if request.method == "POST":
        supplier_id = request.POST.get("supplier")
        order_date = request.POST.get("order_date")
        expected_date = request.POST.get("expected_delivery_date") or None
        quantity_value = request.POST.get("quantity_ordered", "").strip()
        price_value = request.POST.get("unit_price", "").strip()
        remarks = request.POST.get("remarks", "").strip()

        try:
            supplier = get_object_or_404(
                Supplier,
                pk=supplier_id,
                is_active=True,
            )

            quantity = Decimal(quantity_value)
            unit_price = Decimal(price_value)

            if not quantity.is_finite() or quantity <= 0:
                raise ValueError("Order quantity must be greater than zero.")

            if not unit_price.is_finite() or unit_price < 0:
                raise ValueError("Unit price cannot be negative.")

            if quantity > purchase_request.quantity_requested:
                raise ValueError(
                    "Order quantity cannot exceed the purchase request quantity."
                )

            if not order_date:
                raise ValueError("Please select the order date.")

            with transaction.atomic():
                # Lock the request to help prevent duplicate orders.
                locked_request = (
                    MaterialPurchaseRequest.objects
                    .select_for_update()
                    .get(pk=request_id)
                )

                if (
                    locked_request.status != "Pending"
                    or PurchaseOrder.objects.filter(
                        purchase_request=locked_request
                    ).exists()
                ):
                    raise ValueError(
                        "This request has already been processed."
                    )

                PurchaseOrder.objects.create(
                    purchase_request=locked_request,
                    supplier=supplier,
                    order_date=order_date,
                    expected_delivery_date=expected_date,
                    quantity_ordered=quantity,
                    unit_price=unit_price,
                    status="Ordered",
                    remarks=remarks,
                )

                locked_request.status = "Ordered"
                locked_request.save(update_fields=["status"])

            return redirect("purchase:purchase_requests")

        except (ValueError, InvalidOperation) as exc:
            error = str(exc)

    return render(
        request,
        "purchase/create_order.html",
        {
            "purchase_request": purchase_request,
            "suppliers": suppliers,
            "error": error,
        },
    )


def purchase_requests(request):
    requests = (
        MaterialPurchaseRequest.objects
        .select_related("production_plan", "production_plan__production_request")
        .filter(status="Pending")
        .order_by("-created_at")
    )

    return render(
        request,
        "purchase/purchase_requests.html",
        {"purchase_requests": requests},
    )
