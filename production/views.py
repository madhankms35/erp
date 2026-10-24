from django.shortcuts import render
from . models import *
from django.shortcuts import get_object_or_404, render, redirect
from .forms import *
from decimal import Decimal
from django.db.models import Sum
from django.db import transaction
from django.views.decorators.http import require_POST
from store.models import MaterialReceipt    
from logistics.models import FinishedGoods    
# Create your views here.


def production_list(request):
    productions = ProductionRequest.objects.all()
    context = {
        'productions': productions
    }
    return render(request, 'production/production_records.html', context)


def Production_Request(request):
    if request.method == 'POST':
        form = ProductionForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('production:production_list')
    else:
        form = ProductionForm()

    return render(
        request,
        'production/new_request.html',
        {'form': form}
    )



def new_plan(request):
    # Show requests that have not already been planned
    requests_list = ProductionRequest.objects.exclude(
        plans__isnull=False
    ).order_by('-created_at')

    return render(
        request,
        'production/new_plan.html',
        {'requests_list': requests_list}
    )


# def check_materials(request, request_id):
#     production_request = get_object_or_404(
#         ProductionRequest,
#         pk=request_id
#     )
#     requirements = ProductMaterial.objects.filter(
#         product_name=production_request.product
#     )

#     material_rows = []
#     has_shortage = False

#     for item in requirements:
#         required = (
#             item.quantity_per_unit * production_request.quantity
#         )

#         available = MaterialReceipt.objects.filter(
#             material_name=item.material_name,
#             unit=item.unit,
#             status='Accepted'
#         ).aggregate(
#             total=Sum('quantity')
#         )['total'] or Decimal('0')

#         shortage = max(required - available, Decimal('0'))

#         if shortage > 0:
#             has_shortage = True

#         material_rows.append({
#             'material_name': item.material_name,
#             'unit': item.unit,
#             'required': required,
#             'available': available,
#             'shortage': shortage,
#         })

#     return render(
#         request,
#         'production/check_materials.html',
#         {
#             'production_request': production_request,
#             'material_rows': material_rows,
#             'has_shortage': has_shortage,
#         }
#     )


def check_materials(request, request_id):
    production_request = get_object_or_404(
        ProductionRequest, pk=request_id
    )

    material_rows = get_material_rows(production_request)

    has_shortage = any(
        row['shortage'] > 0 for row in material_rows
    )

    return render(request, 'production/check_materials.html', {
        'production_request': production_request,
        'material_rows': material_rows,
        'has_shortage': has_shortage,
    })


@require_POST
def start_production(request, request_id):
    production_request = get_object_or_404(
        ProductionRequest,
        pk=request_id
    )

    # Prevent creating a duplicate plan
    if production_request.plans.exists():
        return redirect('production:production_plans')

    requirements = ProductMaterial.objects.filter(
        product_name=production_request.product
    )

    # Recheck stock on the server before starting
    if not requirements.exists():
        return redirect('check_materials', request_id=request_id)

    for item in requirements:
        required = (
            item.quantity_per_unit * production_request.quantity
        )

        available = MaterialReceipt.objects.filter(
            material_name=item.material_name,
            unit=item.unit,
            status='Accepted'
        ).aggregate(
            total=Sum('quantity')
        )['total'] or Decimal('0')

        if available < required:
            return redirect('check_materials', request_id=request_id)

    ProductionPlan.objects.create(
        production_request=production_request,
        status='Allotted'
    )

    return redirect('production:production_plans')


def production_plans(request):
    plans = ProductionPlan.objects.exclude(status='Completed').select_related('production_request').order_by('-created_at')

    for plan in plans:
        production_request = plan.production_request

        requirements = ProductMaterial.objects.filter(
            product_name=production_request.product
        )

        material_rows = []

        for item in requirements:
            required = (
                item.quantity_per_unit * production_request.quantity
            )

            request_items = MaterialRequestItem.objects.filter(
                material_request__production_plan=plan,
                material_name=item.material_name,
                unit=item.unit,
            )

            issued = request_items.aggregate(
                total=Sum('quantity_issued')
            )['total'] or Decimal('0')

            received = request_items.aggregate(
                total=Sum('quantity_issued')
            )['total'] or Decimal('0')

            accepted_stock = MaterialReceipt.objects.filter(
                material_name=item.material_name,
                unit=item.unit,
                status='Accepted'
            ).aggregate(
                total=Sum('quantity')
            )['total'] or Decimal('0')

            issued_all_plans = MaterialRequestItem.objects.filter(
                material_name=item.material_name,
                unit=item.unit,
            ).aggregate(
                total=Sum('quantity_issued')
            )['total'] or Decimal('0')

            available = max(
                accepted_stock - issued_all_plans,
                Decimal('0')
            )

            balance = max(required - received, Decimal('0'))

            # Issued material is no longer store stock.
            # Do not purchase material already issued to this plan.
            purchase_quantity = max(
                required - issued - available,
                Decimal('0')
            )

            material_rows.append({
                'material_name': item.material_name,
                'unit': item.unit,
                'required': required,
                'issued': issued,
                'received': received,
                'balance': balance,
                'available': available,
                'purchase_quantity': purchase_quantity,
            })

        plan.material_rows = material_rows

    return render(request, 'production/production_plans.html', {
        'plans': plans,
        'status_choices': ProductionPlan.STATUS_CHOICES,
    })




@require_POST
def update_plan_status(request, plan_id):
    with transaction.atomic():
        plan = get_object_or_404(
            ProductionPlan.objects.select_for_update(),
            pk=plan_id
        )

        new_status = request.POST.get('status')
        valid_statuses = dict(ProductionPlan.STATUS_CHOICES)

        if new_status in valid_statuses:
            plan.status = new_status
            plan.remarks = request.POST.get('remarks', '').strip()
            plan.save()

            # Transfer completed production to Logistics.
            if new_status == 'Completed':
                FinishedGoods.objects.get_or_create(
                    production_plan=plan,
                    defaults={
                        'product_name': plan.production_request.product,
                        'quantity_produced': (
                            plan.production_request.quantity
                        ),
                    }
                )

    return redirect('production:production_plans')



def get_material_rows(production_request):
    requirements = ProductMaterial.objects.filter(
        product_name=production_request.product
    )

    material_rows = []

    for item in requirements:
        required = (
            item.quantity_per_unit * production_request.quantity
        )

        available = MaterialReceipt.objects.filter(
            material_name=item.material_name,
            unit=item.unit,
            status='Accepted'
        ).aggregate(
            total=Sum('quantity')
        )['total'] or Decimal('0')

        shortage = max(required - available, Decimal('0'))

        material_rows.append({
            'material_name': item.material_name,
            'unit': item.unit,
            'required': required,
            'available': available,
            'shortage': shortage,
        })

    return material_rows



@require_POST
def request_missing_materials(request, request_id):
    production_request = get_object_or_404(
        ProductionRequest, pk=request_id
    )

    # Prevent creating a second plan for the same request.
    if production_request.plans.exists():
        return redirect('production:production_plans')

    material_rows = get_material_rows(production_request)

    # Do not create an empty material request.
    if not material_rows:
        return redirect('production:check_materials', request_id=request_id)

    has_shortage = any(
        row['shortage'] > 0 for row in material_rows
    )

    with transaction.atomic():
        plan = ProductionPlan.objects.create(
            production_request=production_request,
            status=(
                'Waiting for Materials'
                if has_shortage
                else 'Allotted'
            )
        )

        material_request = MaterialRequest.objects.create(
            production_plan=plan,
            status='Pending',
            remarks='Store request for all materials required for production.'
        )

        for item in material_rows:
            MaterialRequestItem.objects.create(
                material_request=material_request,
                material_name=item['material_name'],
                quantity_requested=item['required'],
                quantity_issued=Decimal('0'),
                quantity_short=item['shortage'],
                unit=item['unit'],
            )

    return redirect('production:production_plans')


@require_POST
def raise_material_purchase_request(request, plan_id):
    plan = get_object_or_404(ProductionPlan, pk=plan_id)
    material_name = request.POST.get('material_name', '').strip()

    requirement = get_object_or_404(
        ProductMaterial,
        product_name=plan.production_request.product,
        material_name=material_name,
    )

    required = (
        requirement.quantity_per_unit
        * plan.production_request.quantity
    )

    items = MaterialRequestItem.objects.filter(
        material_request__production_plan=plan,
        material_name=material_name,
        unit=requirement.unit,
    )

    issued = items.aggregate(
        total=Sum('quantity_issued')
    )['total'] or Decimal('0')

    accepted_stock = MaterialReceipt.objects.filter(
        material_name=material_name,
        unit=requirement.unit,
        status='Accepted',
    ).aggregate(
        total=Sum('quantity')
    )['total'] or Decimal('0')

    all_issued = MaterialRequestItem.objects.filter(
        material_name=material_name,
        unit=requirement.unit,
    ).aggregate(
        total=Sum('quantity_issued')
    )['total'] or Decimal('0')

    available = max(
        accepted_stock - all_issued,
        Decimal('0')
    )

    purchase_quantity = max(
        required - issued - available,
        Decimal('0')
    )

    if purchase_quantity > 0:
        purchase_request, created = (
            MaterialPurchaseRequest.objects.get_or_create(
                production_plan=plan,
                material_name=material_name,
                defaults={
                    'quantity_requested': purchase_quantity,
                    'unit': requirement.unit,
                    'status': 'Pending',
                    'remarks': 'Raised from production plan.',
                },
            )
        )

        # Update an existing request only while it is Pending.
        # Do not overwrite a request already being processed.
        if not created and purchase_request.status == 'Pending':
            purchase_request.quantity_requested = purchase_quantity
            purchase_request.unit = requirement.unit
            purchase_request.save(
                update_fields=[
                    'quantity_requested',
                    'unit',
                    'updated_at',
                ]
            )

    return redirect('production:production_plans')


