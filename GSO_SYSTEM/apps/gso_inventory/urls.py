from django.urls import path
from . import views

app_name = "gso_inventory"

urlpatterns = [
    # GSO Inventory
    path('gso/', views.gso_inventory, name='gso_inventory'),
    path('gso/add/', views.add_inventory_item, name='add_inventory_item'),
    path('gso/update/<int:item_id>/', views.update_inventory_item, name='update_inventory_item'),
    path('gso/remove/<int:item_id>/', views.remove_inventory_item, name='remove_inventory_item'),

    # Unit Head
    path('unit-head/', views.unit_head_inventory, name='unit_head_inventory'),

    # Personnel
    path('personnel/', views.personnel_inventory, name='personnel_inventory'),
]
