
from django.db.models import Sum, Q,F, Value, IntegerField
from .models import *
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.views.decorators.http import require_http_methods


def finished_goods_list(request):
    finished_goods = FinishedGoods.objects.annotate(
    dispatched_quantity=Coalesce(
        Sum(
            'dispatches__quantity',
            filter=Q(dispatches__status='Dispatched')
        ),
        Value(0),
        output_field=IntegerField()
    )
    ).annotate(
    available_quantity=F('quantity_produced') - F('dispatched_quantity')
    ).filter(
    available_quantity__gt=0
    ).select_related(
    'production_plan',
    'production_plan__production_request'
    ).order_by('-received_date')

    for item in finished_goods:
        item.dispatched_quantity = item.dispatched_quantity or 0
        item.available_quantity = (
            item.quantity_produced - item.dispatched_quantity
        )

    return render(
        request,
        'logistics/finished_goods_list.html',
        {'finished_goods': finished_goods}
    )



@require_http_methods(["GET", "POST"])
def dispatch_billing(request):
    error = ""

    if request.method == "POST":
        goods_id = request.POST.get("finished_goods")
        buyer_name = request.POST.get("buyer_name", "").strip()
        invoice_number = request.POST.get("invoice_number", "").strip()
        quantity_text = request.POST.get("quantity", "").strip()

        try:
            goods_id = int(goods_id)
            quantity = int(quantity_text)

            if quantity <= 0:
                raise ValueError
        except (TypeError, ValueError):
            error = "Select valid finished goods and enter a quantity greater than zero."
        else:
            if not buyer_name:
                error = "Buyer name is required."
            else:
                try:
                    with transaction.atomic():
                        goods = get_object_or_404(
                            FinishedGoods.objects.select_for_update(),
                            pk=goods_id
                        )

                        dispatched = goods.dispatches.filter(
                            status="Dispatched"
                        ).aggregate(
                            total=Sum("quantity")
                        )["total"] or 0

                        available = goods.quantity_produced - dispatched

                        if quantity > available:
                            error = (
                                f"Only {available} units are available. "
                                "Reduce the dispatch quantity."
                            )
                        else:
                            Dispatch.objects.create(
                                finished_goods=goods,
                                buyer_name=buyer_name,
                                invoice_number=invoice_number,
                                quantity=quantity,
                                dispatch_date=timezone.localdate(),
                                status="Dispatched",
                            )

                except Exception:
                    raise

                if not error:
                    return redirect("logistics:dispatch_billing")

    finished_goods = FinishedGoods.objects.order_by("-received_date")

    goods_rows = []
    for goods in finished_goods:
        dispatched = goods.dispatches.filter(
            status="Dispatched"
        ).aggregate(
            total=Sum("quantity")
        )["total"] or 0

        available = goods.quantity_produced - dispatched

        if available > 0:
            goods_rows.append({
                "id": goods.id,
                "product_name": goods.product_name,
                "available": available,
            })

    dispatches = Dispatch.objects.select_related(
        "finished_goods"
    ).order_by("-created_at")

    return render(
        request,
        "logistics/dispatch_billing.html",
        {
            "goods_rows": goods_rows,
            "dispatches": dispatches,
            "error": error,
        },
    )
