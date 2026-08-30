from django.urls import path
from . import panel_views

app_name = 'admin_panel'

urlpatterns = [
    path('login/', panel_views.admin_login, name='login'),
    path('logout/', panel_views.admin_logout, name='logout'),
    path('', panel_views.dashboard, name='dashboard'),
    path('users/', panel_views.users_list, name='users'),
    path('users/<int:user_id>/', panel_views.user_detail, name='user_detail'),
    path('agents/create/', panel_views.create_agent, name='create_agent'),
    path('calls/', panel_views.calls_list, name='calls'),
    path('calls/<int:call_id>/', panel_views.call_detail, name='call_detail'),
    path('offers/', panel_views.offers_list, name='offers'),
    path('offers/', panel_views.offers_list, name='offers'),
    path('tasks/', panel_views.task_config, name='tasks'),
    path('settings/', panel_views.settings_list, name='settings'),
    path('withdrawals/', panel_views.withdrawals_list, name='withdrawals'),
    path('withdrawals/<int:request_id>/<str:action>/', panel_views.handle_withdrawal, name='handle_withdrawal'),
    path('transactions/', panel_views.transactions_list, name='transactions'),
]
