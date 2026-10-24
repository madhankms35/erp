from django.shortcuts import render, redirect, get_object_or_404
from .forms import MaterialReceiptForm
from production.models import *
from purchase.models import *
from decimal import Decimal, InvalidOperation
from .models import *
from django.db import transaction
from django.db.models import Sum
from django.contrib import messages

def add_material(request):
    if request.method == "POST":
        form = MaterialReceiptForm(request.POST)

        if form.is_valid():
            selected_po = form.cleaned_data["purchase_order"]

            with transaction.atomic():
                # Lock the PO while checking and saving its receipt.
                po = get_object_or_404(
                    PurchaseOrder.objects.select_for_update(),
                    pk=selected_po.pk,
                )

                if po.status not in ["Ordered", "Partially Received"]:
                    form.add_error(
                        "purchase_order",
                        "This purchase order is no longer open."
                    )
                else:
                    # Count all previous inward entries for this PO,
                    # including entries still awaiting inspection.
                    previous_received = (
                        MaterialReceipt.objects.filter(
                            purchase_order=po
                        ).aggregate(
                            total=Sum("quantity")
                        )["total"] or Decimal("0")
                    )

                    incoming_quantity = form.cleaned_data["quantity"]

                    balance = (
                        po.quantity_ordered - previous_received
                    )

                    if incoming_quantity > balance:
                        form.add_error(
                            "quantity",
                            f"Only {balance} {po.purchase_request.unit} "
                            "can be received against this PO."
                        )
                    else:
                        receipt = form.save(commit=False)

                        # Get these details from the selected PO.
                        receipt.purchase_order = po
                        receipt.purchase_order_number = str(po.pk)
                        receipt.material_name = (
                            po.purchase_request.material_name
                        )
                        receipt.supplier = po.supplier.name
                        receipt.unit = po.purchase_request.unit

                        receipt.save()

                        total_received = previous_received + incoming_quantity

                        if total_received >= po.quantity_ordered:
                            po.status = "Received"
                            po.purchase_request.status = "Received"
                            po.purchase_request.save(
                                update_fields=["status", "updated_at"]
                            )
                        else:
                            po.status = "Partially Received"

                        po.save(update_fields=["status", "updated_at"])

                        messages.success(
                            request,
                            f"Inward saved for PO #{po.pk}. "
                            f"Total received: {total_received}; "
                            f"balance: {po.quantity_ordered - total_received}."
                        )

                        return redirect("add_material")

    else:
        form = MaterialReceiptForm()

    # Details used to show the selected PO's material, supplier,
    # ordered quantity, received quantity and balance on the page.
    purchase_orders = PurchaseOrder.objects.filter(
        status__in=["Ordered", "Partially Received"]
    ).select_related(
        "supplier", "purchase_request"
    ).order_by("id")

    po_details = []

    for po in purchase_orders:
        already_received = (
            MaterialReceipt.objects.filter(
                purchase_order=po
            ).aggregate(
                total=Sum("quantity")
            )["total"] or Decimal("0")
        )

        po_details.append({
            "id": po.pk,
            "material": po.purchase_request.material_name,
            "supplier": po.supplier.name,
            "ordered": str(po.quantity_ordered),
            "received": str(already_received),
            "balance": str(
                max(po.quantity_ordered - already_received, Decimal("0"))
            ),
            "unit": po.purchase_request.unit,
        })

    return render(
        request,
        "store/add_material.html",
        {
            "form": form,
            "po_details": po_details,
        }
    )


def get_issue_rows(material_request):
    rows = []

    items = MaterialRequestItem.objects.filter(
        material_request=material_request
    ).order_by("id")

    for item in items:
        # Actual issued quantity from Store's records
        issued = (
            StoreMaterialIssueItem.objects.filter(
                material_request_item=item
            ).aggregate(total=Sum("quantity_issued"))["total"]
            or Decimal("0")
        )

        # Accepted incoming stock
        received_stock = (
            MaterialReceipt.objects.filter(
                material_name=item.material_name,
                unit=item.unit,
                status="Accepted",
            ).aggregate(total=Sum("quantity"))["total"]
            or Decimal("0")
        )

        # All issues of this material across all production requests
        all_issued = (
            StoreMaterialIssueItem.objects.filter(
                material_request_item__material_name=item.material_name,
                unit=item.unit,
            ).aggregate(total=Sum("quantity_issued"))["total"]
            or Decimal("0")
        )

        available = max(
            received_stock - all_issued,
            Decimal("0")
        )

        rows.append({
            "item": item,
            "issued": issued,
            "remaining": max(
                item.quantity_requested - issued,
                Decimal("0")
            ),
            "available": available,
        })

    return rows


def material_issue(request):
    request_id = (
        request.POST.get("request_id")
        if request.method == "POST"
        else request.GET.get("request_id")
    )

    material_request = None
    rows = []
    error = ""

    if request_id:
        try:
            material_request = get_object_or_404(
                MaterialRequest,
                pk=int(request_id)
            )
        except (ValueError, TypeError):
            error = "Enter a valid Material Request ID."

    if material_request:
        rows = get_issue_rows(material_request)

    if request.method == "POST" and material_request:
        try:
            quantities = []
            requested_by_material = {}

            for row in rows:
                item = row["item"]
                raw_value = request.POST.get(
                    f"issue_{item.id}", "0"
                ).strip()

                quantity = Decimal(raw_value or "0")

                if not quantity.is_finite() or quantity < 0:
                    raise ValueError(
                        f"Invalid quantity for {item.material_name}."
                    )

                if quantity > row["remaining"]:
                    raise ValueError(
                        f"Issue quantity for {item.material_name} "
                        "cannot exceed the remaining request."
                    )

                key = (item.material_name, item.unit)
                requested_by_material[key] = (
                    requested_by_material.get(key, Decimal("0"))
                    + quantity
                )

                quantities.append((item, quantity))

            # Check combined quantities against stock before saving.
            for (material_name, unit), quantity in (
                requested_by_material.items()
            ):
                stock = (
                    MaterialReceipt.objects.filter(
                        material_name=material_name,
                        unit=unit,
                        status="Accepted",
                    ).aggregate(total=Sum("quantity"))["total"]
                    or Decimal("0")
                )

                already_issued = (
                    StoreMaterialIssueItem.objects.filter(
                        material_request_item__material_name=material_name,
                        unit=unit,
                    ).aggregate(total=Sum("quantity_issued"))["total"]
                    or Decimal("0")
                )

                available = max(
                    stock - already_issued,
                    Decimal("0")
                )

                if quantity > available:
                    raise ValueError(
                        f"Insufficient stock for {material_name}. "
                        f"Available: {available} {unit}."
                    )

            if not any(qty > 0 for _, qty in quantities):
                raise ValueError(
                    "Enter at least one quantity greater than zero."
                )

            with transaction.atomic():
                issue = StoreMaterialIssue.objects.create(
                    material_request=material_request,
                    remarks=request.POST.get("remarks", "").strip(),
                )

                for item, quantity in quantities:
                    if quantity == 0:
                        continue

                    StoreMaterialIssueItem.objects.create(
                        store_issue=issue,
                        material_request_item=item,
                        quantity_issued=quantity,
                        unit=item.unit,
                    )

                    # Maintain the existing field for Production's display.
                    total_issued = (
                        StoreMaterialIssueItem.objects.filter(
                            material_request_item=item
                        ).aggregate(total=Sum("quantity_issued"))["total"]
                        or Decimal("0")
                    )

                    item.quantity_issued = total_issued
                    item.save(update_fields=["quantity_issued"])

                # Close as fulfilled only when every item is fully issued.
                all_items = MaterialRequestItem.objects.filter(
                    material_request=material_request
                )

                fully_issued = all(
                    item.quantity_issued >= item.quantity_requested
                    for item in all_items
                )

                material_request.status = (
                    "Fulfilled" if fully_issued
                    else "Partially Fulfilled"
                )
                material_request.save(update_fields=["status"])

            return redirect("store:material_issue")

        except (ValueError, InvalidOperation) as exc:
            error = str(exc)

        except Exception:
            error = (
                "The issue could not be saved. Check the server error "
                "for details and verify your model fields."
            )

    return render(
        request,
        "store/material_issue.html",
        {
            "material_request": material_request,
            "rows": rows,
            "error": error,
            "request_id": request_id or "",
        },
    )


def location_assignment(request):
    receipts = MaterialReceipt.objects.filter(
        status="Accepted"
    ).order_by("inward_date", "id")

    if request.method == "POST":
        receipt_id = request.POST.get("receipt_id")
        location = request.POST.get("location", "").strip()

        receipt = get_object_or_404(
            MaterialReceipt,
            pk=receipt_id,
            status="Accepted",
        )

        if not location:
            messages.error(request, "Enter a storage location.")
        else:
            receipt.location = location
            receipt.save(update_fields=["location", "updated_at"])

            messages.success(
                request,
                f"Location saved for receipt #{receipt.id}."
            )

        return redirect("location_assignment")

    return render(
        request,
        "store/assign_location.html",
        {"receipts": receipts},
    )
    