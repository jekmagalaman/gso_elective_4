from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from apps.gso_accounts.models import Unit, User
from django.db.models import Q
from .models import InventoryItem
from .forms import InventoryItemForm

# -------------------------------
# Helper role checks
# -------------------------------
def is_unit_head(user):
    return user.is_authenticated and getattr(user, "role", None) == "unit_head"

def is_gso(user):
    return user.is_authenticated and getattr(user, "role", None) == "gso"

def is_director(user):
    return user.is_authenticated and getattr(user, "role", None) == "director"

# Combined check for GSO + Director
def can_access_inventory(user):
    return is_gso(user) or is_director(user)

# -------------------------------
# GSO / Director Inventory Views
# -------------------------------
@login_required
@user_passes_test(can_access_inventory)
def gso_inventory(request):
    """
    Shows full inventory for GSO and Director roles.
    """
    category = request.GET.get("category")
    query = request.GET.get("q")

    items = InventoryItem.objects.all()
    if category:
        items = items.filter(category=category)
    if query:
        items = items.filter(
            Q(name__icontains=query) |
            Q(category__icontains=query) |
            Q(description__icontains=query)
        )

    items = items.order_by("name")
    categories = InventoryItem.objects.values_list("category", flat=True).distinct()

    forms_per_item = {item.id: InventoryItemForm(instance=item) for item in items}

    return render(request, "gso_office/inventory/gso_inventory.html", {
        "inventory_items": items,
        "categories": categories,
        "selected_category": category,
        "search_query": query,
        "form": InventoryItemForm(),
        "forms_per_item": forms_per_item,
    })

@login_required
@user_passes_test(can_access_inventory)
def add_inventory_item(request):
    if request.method == "POST":
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            form.save()
    return redirect("gso_inventory:gso_inventory")

@login_required
@user_passes_test(can_access_inventory)
def update_inventory_item(request, item_id):
    item = get_object_or_404(InventoryItem, id=item_id)
    if request.method == "POST":
        form = InventoryItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
    return redirect("gso_inventory:gso_inventory")

@login_required
@user_passes_test(can_access_inventory)
def remove_inventory_item(request, item_id):
    item = get_object_or_404(InventoryItem, id=item_id)
    if request.method == "POST":
        item.delete()
    return redirect("gso_inventory:gso_inventory")

# -------------------------------
# Unit Head Inventory
# -------------------------------
@login_required
@user_passes_test(is_unit_head)
def unit_head_inventory(request):
    """
    Show inventory items belonging only to the unit head's unit.
    """
    unit = request.user.unit
    items = InventoryItem.objects.filter(is_active=True, owned_by=unit)

    # Search filter
    search_query = request.GET.get("q")
    if search_query:
        items = items.filter(
            Q(name__icontains=search_query) |
            Q(category__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    items = items.order_by("name")
    categories = InventoryItem.objects.filter(owned_by=unit).values_list("category", flat=True).distinct()

    return render(request, "unit_heads/unit_head_inventory/unit_head_inventory.html", {
        "inventory_items": items,
        "categories": categories,
        "search_query": search_query,
    })

# -------------------------------
# Personnel Inventory (placeholder)
# -------------------------------
@login_required
def personnel_inventory(request):
    # Currently personnel cannot see inventory
    return render(request, "personnel/personnel_inventory/personnel_inventory.html")
