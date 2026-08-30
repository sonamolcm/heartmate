from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from .models import User, CallHistory, Offer, AgentTaskConfig, GlobalSetting, WithdrawalRequest, Wallet, Transaction

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
    tab = request.GET.get('tab', 'all')
    
    queryset = User.objects.filter(is_superuser=False).order_by('-date_joined')
    
    if tab == 'users':
        queryset = queryset.filter(is_staff=False)
    elif tab == 'agents':
        queryset = queryset.filter(is_staff=True)
        
    return render(request, 'admin_panel/users.html', {'users': queryset, 'active_tab': tab})

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

@user_passes_test(is_superadmin, login_url='admin_panel:login')
def create_agent(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone_number')
        password = request.POST.get('password')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.phone_number = phone
            user.is_staff = True
            user.save()
            messages.success(request, 'Agent created successfully!')
            return redirect('admin_panel:users')
            
    return render(request, 'admin_panel/create_agent.html')

@user_passes_test(is_superadmin, login_url='admin_panel:login')
def task_config(request):
    config = AgentTaskConfig.load()
    if request.method == 'POST':
        config.daily_call_target = request.POST.get('daily_target', 50)
        config.weekly_call_target = request.POST.get('weekly_target', 250)
        config.monthly_call_target = request.POST.get('monthly_target', 1000)
        config.save()
        messages.success(request, 'Task configuration updated!')
        return redirect('admin_panel:tasks')
        
    return render(request, 'admin_panel/task_config.html', {'config': config})

@user_passes_test(is_superadmin, login_url='admin_panel:login')
def settings_list(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            key = request.POST.get('key')
            value = request.POST.get('value')
            data_type = request.POST.get('data_type')
            desc = request.POST.get('description')
            if not GlobalSetting.objects.filter(key=key).exists():
                GlobalSetting.objects.create(key=key, value=value, data_type=data_type, description=desc)
                messages.success(request, 'Setting created successfully!')
            else:
                messages.error(request, 'Setting with this key already exists.')
        elif action == 'update':
            setting_id = request.POST.get('setting_id')
            value = request.POST.get('value')
            setting = GlobalSetting.objects.get(id=setting_id)
            setting.value = value
            setting.save()
            messages.success(request, 'Setting updated successfully!')
        return redirect('admin_panel:settings')
        
    settings = GlobalSetting.objects.all().order_by('key')
    return render(request, 'admin_panel/settings.html', {'settings': settings})

@user_passes_test(is_superadmin, login_url='admin_panel:login')
def withdrawals_list(request):
    requests = WithdrawalRequest.objects.all().order_by('-created_at')
    return render(request, 'admin_panel/withdrawals.html', {'requests': requests})

@user_passes_test(is_superadmin, login_url='admin_panel:login')
def handle_withdrawal(request, request_id, action):
    try:
        withdrawal = WithdrawalRequest.objects.get(id=request_id)
        if withdrawal.status != 'pending':
            messages.error(request, 'This request has already been processed.')
            return redirect('admin_panel:withdrawals')
            
        if action == 'approve':
            withdrawal.status = 'approved'
            withdrawal.save()
            messages.success(request, f'Approved withdrawal for {withdrawal.agent.username}')
            
        elif action == 'reject':
            # Refund the wallet
            wallet = withdrawal.agent.wallet
            wallet.balance += withdrawal.amount
            wallet.save()
            
            # Log refund transaction
            Transaction.objects.create(
                user=withdrawal.agent,
                amount=withdrawal.amount,
                transaction_type='earn_call', # or 'refund'
                reference_id=f"refund_{withdrawal.id}"
            )
            
            withdrawal.status = 'rejected'
            withdrawal.save()
            messages.success(request, f'Rejected withdrawal for {withdrawal.agent.username} and refunded {withdrawal.amount} coins.')
            
    except WithdrawalRequest.DoesNotExist:
        messages.error(request, 'Request not found.')
        
    return redirect('admin_panel:withdrawals')

@user_passes_test(is_superadmin, login_url='admin_panel:login')
def transactions_list(request):
    tab_type = request.GET.get('type', 'all')
    
    if tab_type == 'earn_call':
        transactions = Transaction.objects.filter(transaction_type='earn_call')
    elif tab_type == 'withdrawal':
        transactions = Transaction.objects.filter(transaction_type='withdrawal')
    elif tab_type == 'coin_purchase':
        transactions = Transaction.objects.filter(transaction_type='coin_purchase')
    else:
        transactions = Transaction.objects.all()
        tab_type = 'all'
        
    transactions = transactions.order_by('-created_at')
    
    return render(request, 'admin_panel/transactions.html', {
        'transactions': transactions,
        'current_tab': tab_type
    })
