
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from store.models import MaterialReceipt


def inspection_list(request):
    receipts = MaterialReceipt.objects.filter(
        status="Pending Inspection"
    ).order_by("inward_date", "id")

    return render(
        request,
        "qc/inspection_list.html",
        {"receipts": receipts},
    )


@require_POST
def update_inspection(request, receipt_id):
    receipt = get_object_or_404(
        MaterialReceipt,
        pk=receipt_id,
        status="Pending Inspection",
    )

    decision = request.POST.get("decision")

    if decision not in ["Accepted", "Rejected"]:
        messages.error(request, "Choose Accept or Reject.")
        return redirect("qc:inspection_list")

    receipt.status = decision
    receipt.save(update_fields=["status", "updated_at"])

    messages.success(
        request,
        f"Receipt #{receipt.id} marked {decision.lower()}."
    )

    return redirect("qc:inspection_list")
