# apps/gso_requests/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseForbidden

from .models import ServiceRequest, RequestMaterial, Unit, TaskReport
from apps.gso_accounts.models import User
from apps.gso_inventory.models import InventoryItem
from .utils import filter_requests, get_unit_inventory, create_war_from_request


# -------------------------------
# Role checks
# -------------------------------
def is_gso(user): return user.is_authenticated and user.role == "gso"
def is_unit_head(user): return user.is_authenticated and user.role == "unit_head"
def is_requestor(user): return user.is_authenticated and user.role == "requestor"
def is_director(user): return user.is_authenticated and user.role == "director"


# -------------------------------
# GSO Office Views
# -------------------------------
@login_required
@user_passes_test(is_gso)
def request_management(request):
    requests_qs = ServiceRequest.objects.select_related("requestor", "unit").prefetch_related("assigned_personnel").order_by("-created_at")

    # Apply filters
    requests_qs = filter_requests(
        requests_qs,
        search_query=request.GET.get("q"),
        unit_filter=request.GET.get("unit"),
    )

    units = Unit.objects.all()
    return render(request, "gso_office/request_management/request_management.html", {
        "requests": requests_qs,
        "units": units,
        "search_query": request.GET.get("q"),
        "unit_filter": request.GET.get("unit"),
    })


# -------------------------------
# Director Views
# -------------------------------
@login_required
@user_passes_test(is_director)
def director_request_management(request):
    requests_qs = ServiceRequest.objects.select_related("requestor", "unit").prefetch_related("assigned_personnel").order_by("-created_at")

    # Apply filters
    requests_qs = filter_requests(
        requests_qs,
        search_query=request.GET.get("q"),
        unit_filter=request.GET.get("unit"),
    )

    units = Unit.objects.all()
    return render(request, "director/director_request_management.html", {
        "requests": requests_qs,
        "units": units,
        "search_query": request.GET.get("q"),
        "unit_filter": request.GET.get("unit"),
    })


@login_required
@user_passes_test(is_director)
def approve_request(request, pk):
    req = get_object_or_404(ServiceRequest, pk=pk)
    if req.status != "Pending":
        return HttpResponseForbidden("This request cannot be approved.")

    req.status = "Approved"
    req.save()
    return redirect("gso_requests:director_request_management")


# -------------------------------
# Unit Head Views
# -------------------------------
@login_required
@user_passes_test(is_unit_head)
def unit_head_request_management(request):
    requests_qs = ServiceRequest.objects.filter(
        unit=request.user.unit
    ).exclude(status__in=["Completed", "Cancelled"]).order_by("-created_at")

    # Apply filters
    requests_qs = filter_requests(
        requests_qs,
        search_query=request.GET.get("q"),
        status_filter=request.GET.get("status"),
    )

    return render(request, "unit_heads/unit_head_request_management/unit_head_request_management.html", {
        "requests": requests_qs
    })


@login_required
@user_passes_test(is_unit_head)
def unit_head_request_detail(request, pk):
    service_request = get_object_or_404(ServiceRequest, pk=pk)
    personnel = User.objects.filter(role="personnel", unit=service_request.unit)
    materials = InventoryItem.objects.filter(is_active=True)
    reports = service_request.reports.select_related("personnel").order_by("-created_at")

    if request.method == "POST":
        action = request.POST.get("action")

        # Assign Personnel & Materials
        if action == "assign" and service_request.status not in ["Done for Review", "Completed"]:
            service_request.assigned_personnel.set(request.POST.getlist("personnel_ids"))

            # Reset + update materials
            for rm in service_request.requestmaterial_set.all():
                rm.material.quantity += rm.quantity
                rm.material.save()
            service_request.requestmaterial_set.all().delete()

            for mid in request.POST.getlist("material_ids"):
                material = get_object_or_404(InventoryItem, pk=mid)
                qty = int(request.POST.get(f"quantity_{mid}", 1))
                if material.quantity < qty:
                    messages.error(request, f"Not enough {material.name}.")
                    return redirect("gso_requests:unit_head_request_detail", pk=pk)
                material.quantity -= qty
                material.save()
                RequestMaterial.objects.create(request=service_request, material=material, quantity=qty)

            messages.success(request, "Assignments updated successfully.")
            return redirect("gso_requests:unit_head_request_detail", pk=pk)

        # Approve Completion → Auto-generate WAR
        elif action == "approve" and service_request.status == "Done for Review":
            service_request.status = "Completed"
            service_request.completed_at = timezone.now()
            service_request.save()

            # ✅ WAR creation
            create_war_from_request(service_request)

            messages.success(request, "Request marked as Completed. WAR created.")
            return redirect("gso_requests:unit_head_request_detail", pk=pk)

        # Reject Completion
        elif action == "reject" and service_request.status == "Done for Review":
            service_request.status = "In Progress"
            service_request.save()
            messages.warning(request, "Request sent back to In Progress.")
            return redirect("gso_requests:unit_head_request_detail", pk=pk)

    return render(request, "unit_heads/unit_head_request_management/request_detail.html", {
        "req": service_request,
        "personnel": personnel,
        "materials": materials,
        "reports": reports,
    })


@login_required
@user_passes_test(is_unit_head)
def unit_head_request_history(request):
    requests_qs = ServiceRequest.objects.filter(
        unit=request.user.unit,
        status__in=["Completed", "Cancelled"]
    ).order_by("-created_at")

    requests_qs = filter_requests(requests_qs, search_query=request.GET.get("q"))
    return render(request, "unit_heads/unit_head_request_history/unit_head_request_history.html", {
        "requests": requests_qs
    })


@login_required
@user_passes_test(is_unit_head)
def unit_head_inventory(request):
    materials = get_unit_inventory(request.user.unit, search_query=request.GET.get("q"))
    return render(request, "unit_heads/unit_head_inventory/unit_head_inventory.html", {
        "materials": materials
    })


# -------------------------------
# Personnel Views
# -------------------------------
@login_required
def personnel_task_management(request):
    tasks = ServiceRequest.objects.filter(assigned_personnel=request.user).exclude(status__in=["Completed", "Cancelled"]).distinct()
    tasks = filter_requests(tasks, search_query=request.GET.get("q"), status_filter=request.GET.get("status"))
    return render(request, "personnel/personnel_task_management/personnel_task_management.html", {"tasks": tasks})


@login_required
def personnel_task_detail(request, pk):
    task = get_object_or_404(ServiceRequest, pk=pk, assigned_personnel=request.user)
    materials = task.requestmaterial_set.select_related("material")
    reports = task.reports.select_related("personnel").order_by("-created_at")

    if request.method == "POST":
        if "start" in request.POST and task.status == "Approved":
            task.status = "In Progress"
            task.started_at = timezone.now()
            task.save()
        elif "done" in request.POST and task.status == "In Progress":
            task.status = "Done for Review"
            task.done_at = timezone.now()
            task.save()
        elif "add_report" in request.POST:
            report_text = request.POST.get("report_text", "").strip()
            if report_text:
                TaskReport.objects.create(request=task, personnel=request.user, report_text=report_text)
        return redirect("gso_requests:personnel_task_detail", pk=task.id)

    return render(request, "personnel/personnel_task_management/personnel_task_detail.html", {
        "task": task, "materials": materials, "reports": reports
    })


@login_required
def personnel_history(request):
    history = ServiceRequest.objects.filter(assigned_personnel=request.user, status="Completed").order_by("-created_at")
    return render(request, "personnel/personnel_history/personnel_history.html", {"history": history})


@login_required
def personnel_inventory(request):
    materials = get_unit_inventory(request.user.unit, search_query=request.GET.get("q"))
    return render(request, "personnel/personnel_inventory/personnel_inventory.html", {"materials": materials})


# -------------------------------
# Requestor Views
# -------------------------------
@login_required
@user_passes_test(is_requestor)
def requestor_request_management(request):
    requests_qs = ServiceRequest.objects.filter(requestor=request.user).order_by("-created_at")
    units = Unit.objects.all()
    return render(request, "requestor/requestor_request_management/requestor_request_management.html", {
        "requests": requests_qs,
        "units": units,
    })


@login_required
@user_passes_test(is_requestor)
def add_request(request):
    if request.method == "POST":
        ServiceRequest.objects.create(
            requestor=request.user,
            unit_id=request.POST.get("unit"),
            description=request.POST.get("description"),
            status="Pending",
            department=request.user.department,
            custom_full_name=request.POST.get("custom_full_name") or "",
            custom_email=request.POST.get("custom_email") or "",
            custom_contact_number=request.POST.get("custom_contact_number") or "",
        )
        return redirect("gso_requests:requestor_request_management")


@login_required
@user_passes_test(is_requestor)
def cancel_request(request, pk):
    req = get_object_or_404(ServiceRequest, pk=pk, requestor=request.user)
    if req.status in ["Pending", "Approved"]:
        req.status = "Cancelled"
        req.save()
    return redirect("gso_requests:requestor_request_management")


@login_required
@user_passes_test(is_requestor)
def requestor_request_history(request):
    history = ServiceRequest.objects.filter(
        requestor=request.user,
        status__in=["Completed", "Cancelled"]
    ).order_by("-created_at")
    return render(request, "requestor/requestor_request_history/requestor_request_history.html", {
        "request_history": history
    })
