from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Notification
from django.contrib import messages

@login_required
def notification_list(request):
    """Show all notifications for logged-in user"""
    notifications = request.user.notifications.all().order_by("-created_at")
    return render(request, "notifications/notification_list.html", {"notifications": notifications})

@login_required
def mark_as_read(request, notification_id):
    """Mark a notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    messages.success(request, "Notification marked as read.")
    return redirect("notification_list")

@login_required
def mark_all_as_read(request):
    """Mark all notifications for user as read"""
    request.user.notifications.filter(is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect("notification_list")
