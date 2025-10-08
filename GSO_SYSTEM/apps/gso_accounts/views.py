from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.db.models import Q
from .forms import UserEditForm, RequestorProfileUpdateForm, UserForm

User = get_user_model()

# -------------------------------
# Role Redirect
# -------------------------------
@login_required
def role_redirect(request):
    role_map = {
        "director": "gso_requests:director_request_management",
        "gso": "gso_requests:request_management",
        "unit_head": "gso_requests:unit_head_request_management",
        "personnel": "gso_requests:personnel_task_management",
        "requestor": "gso_requests:requestor_request_management",
    }
    target = role_map.get(request.user.role)
    if target:
        return redirect(target)
    return redirect("gso_accounts:login")



# -------------------------------
# GSO Account Management
# -------------------------------
@login_required
def account_management(request):
    users = User.objects.all()

    # Status filter
    status_filter = request.GET.get("status")
    if status_filter:
        users = users.filter(account_status=status_filter)

    # Search filter
    search_query = request.GET.get("q")
    if search_query:
        users = users.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(username__icontains=search_query)
        )

    return render(request, "gso_office/accounts/account_management.html", {"users": users})

@login_required
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)

            # Password update
            new_pass = form.cleaned_data.get("new_password")
            confirm_pass = form.cleaned_data.get("confirm_password")

            if new_pass:
                if new_pass == confirm_pass:
                    user.set_password(new_pass)
                else:
                    form.add_error("confirm_password", "Passwords do not match.")
                    return render(request, "gso_office/accounts/account_edit.html", {"form": form, "user": user})

            user.save()
            return redirect("gso_accounts:account_management")
    else:
        form = UserEditForm(instance=user)

    return render(request, "gso_office/accounts/account_edit.html", {"form": form, "user": user})

@login_required
def add_user(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.password = make_password(form.cleaned_data["password"])
            user.save()
            return redirect("gso_accounts:account_management")
    else:
        form = UserForm()
    return render(request, "gso_office/accounts/add_user.html", {"form": form})







# -------------------------------
# Requestor Views
# -------------------------------
@login_required
def requestor_account(request):
    return render(request, "requestor/requestor_account/requestor_account.html")

@login_required
def profile(request):
    if request.method == "POST":
        form = RequestorProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("gso_accounts:requestor_account")
    else:
        form = RequestorProfileUpdateForm(instance=request.user)
    return render(request, "requestor/account.html", {"form": form})

@login_required
def search_personnel(request):
    """AJAX endpoint: search active personnel by name."""
    query = request.GET.get("q", "").strip()
    results = []
    if query:
        personnel = User.objects.filter(
            role="personnel",
            account_status="active"
        ).filter(Q(first_name__icontains=query) | Q(last_name__icontains=query))[:10]

        results = [{"id": p.id, "name": f"{p.first_name} {p.last_name}"} for p in personnel]

    return JsonResponse(results, safe=False)


# -------------------------------
# Dashboard Views
# -------------------------------
@login_required
def director_dashboard(request):
    # Redirect director immediately to their request management page
    return redirect("gso_requests:director_request_management")

@login_required
def gso_dashboard(request):
    # Redirect to GSO Office request management
    return redirect("gso_requests:request_management")  

@login_required
def unit_head_dashboard(request):
    # Redirect to Unit Head request management
    return redirect("gso_requests:unit_head_request_management")

@login_required
def personnel_dashboard(request):
    # Redirect to Personnel task management
    return redirect("gso_requests:personnel_task_management")

@login_required
def requestor_dashboard(request):
    # Redirect to Requestor request management
    return redirect("gso_accounts:requestor_request_management")
