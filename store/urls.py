from django.urls import path
from . import views
app_name='store'
urlpatterns = [
    path('add-material/', views.add_material, name='add_material'),
    path('material-issue/', views.material_issue, name='material_issue'),
    path("location-assignment/",views.location_assignment,name="location_assignment"),
]