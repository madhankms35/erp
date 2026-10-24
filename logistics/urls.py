
from django.urls import path
from . import views

app_name = 'logistics'

urlpatterns = [
    path(
        'finished-goods/',
        views.finished_goods_list,
        name='finished_goods_list'
    ),
    path(
    "dispatch-billing/",
    views.dispatch_billing,
    name="dispatch_billing"
),
]
