from django.urls import path
from . import views
app_name = 'production'
urlpatterns = [
    path('production_record/',views.production_list,name='production_list'),
    path('new/',views.Production_Request,name='productionrequest'),    
    path('new-plan/', views.new_plan, name='new_plan'),
    path('check-materials/<int:request_id>/', views.check_materials, name='check_materials'),
    path('start-production/<int:request_id>/', views.start_production, name='start_production'),
    path('plans/', views.production_plans, name='production_plans'),
    path('plans/<int:plan_id>/status/', views.update_plan_status, name='update_plan_status'),
    path('request-materials/<int:request_id>/', views.request_missing_materials, name='request_missing_materials'),
    path('plans/<int:plan_id>/raise-purchase/', views.raise_material_purchase_request, name='raise_material_purchase_request'),
]