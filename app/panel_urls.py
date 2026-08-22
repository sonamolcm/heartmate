from django.urls import path
from . import panel_views

app_name = 'admin_panel'

urlpatterns = [
    path('login/', panel_views.admin_login, name='login'),
    path('logout/', panel_views.admin_logout, name='logout'),
    path('', panel_views.dashboard, name='dashboard'),
    path('users/', panel_views.users_list, name='users'),
    path('users/<int:user_id>/', panel_views.user_detail, name='user_detail'),
    path('calls/', panel_views.calls_list, name='calls'),
    path('calls/<int:call_id>/', panel_views.call_detail, name='call_detail'),
    path('offers/', panel_views.offers_list, name='offers'),
]
