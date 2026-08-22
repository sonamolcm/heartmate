from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from .models import User, CallHistory, Offer

def is_superadmin(user):
    return user.is_authenticated and user.is_superuser

def admin_login(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('admin_panel:dashboard')
        
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            if user.is_superuser:
                auth_login(request, user)
                return redirect('admin_panel:dashboard')
            else:
                messages.error(request, 'Only superadmins are allowed to access this panel.')
        else:
            messages.error(request, 'Invalid username or password.')
            
    return render(request, 'admin_panel/login.html')

def admin_logout(request):
    auth_logout(request)
    return redirect('admin_panel:login')

@user_passes_test(is_superadmin, login_url='admin_panel:login')
def dashboard(request):
    total_users = User.objects.filter(is_superuser=False).count()
    total_calls = CallHistory.objects.count()
    active_users = User.objects.filter(is_superuser=False, is_online=True).count()
    
    # recent calls
    recent_calls = CallHistory.objects.order_by('-start_time')[:5]
    
    context = {
        'total_users': total_users,
        'total_calls': total_calls,
        'active_users': active_users,
        'recent_calls': recent_calls,
    }
    return render(request, 'admin_panel/dashboard.html', context)

@user_passes_test(is_superadmin, login_url='admin_panel:login')
def users_list(request):
    users = User.objects.filter(is_superuser=False).order_by('-date_joined')
    return render(request, 'admin_panel/users.html', {'users': users})

@user_passes_test(is_superadmin, login_url='admin_panel:login')
def user_detail(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    return render(request, 'admin_panel/user_detail.html', {'target_user': target_user})

@user_passes_test(is_superadmin, login_url='admin_panel:login')
def calls_list(request):
    calls = CallHistory.objects.select_related('caller', 'receiver').order_by('-start_time')
    return render(request, 'admin_panel/calls.html', {'calls': calls})

@user_passes_test(is_superadmin, login_url='admin_panel:login')
def call_detail(request, call_id):
    target_call = get_object_or_404(CallHistory.objects.select_related('caller', 'receiver'), id=call_id)
    return render(request, 'admin_panel/call_detail.html', {'target_call': target_call})

@user_passes_test(is_superadmin, login_url='admin_panel:login')
def offers_list(request):
    offers = Offer.objects.all().order_by('-created_at')
    return render(request, 'admin_panel/offers.html', {'offers': offers})
