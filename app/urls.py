from django.urls import path
from . import views

urlpatterns = [
    # Authentication URLs
    path('api/register/', views.register_user, name='register'),
    path('api/google-auth/', views.google_auth, name='google_auth'),
    path('api/phone-auth/', views.phone_auth, name='phone_auth'),
    path('api/login/', views.user_login, name='login'),
    path('api/logout/', views.user_logout, name='logout'),
    
    # Profile URLs
    path('api/profile/', views.user_profile, name='user_profile'),
    path('api/profile/<int:user_id>/', views.get_user_profile, name='get_user_profile'),
    path('api/update-status/', views.update_user_status, name='update_user_status'),
    
    # Menu URLs
    path('api/menu/', views.menu_items, name='menu_items'),
    path('api/terms-conditions/', views.get_terms_conditions, name='terms_conditions'),
    path('api/privacy-policy/', views.get_privacy_policy, name='privacy_policy'),
    path('api/help-line/', views.get_help_line, name='help_line'),
    
    # User Listing URLs
    path('api/online-users/', views.get_online_users, name='online_users'),
    path('api/on-call-users/', views.get_on_call_users, name='on_call_users'),
    path('api/users/', views.get_all_users, name='all_users'),
    
    # Coin and Offers URLs
    path('api/coins/', views.get_user_coins, name='user_coins'),
    path('api/coins/add/', views.add_coins, name='add_coins'),
    path('api/coins/deduct/', views.deduct_coins, name='deduct_coins'),
    path('api/offers/', views.get_active_offers, name='active_offers'),
    path('api/offers/<int:offer_id>/', views.get_offer_detail, name='offer_detail'),
    path('api/offers/<int:offer_id>/redeem/', views.redeem_offer, name='redeem_offer'),
    
    # FCM & Call URLs
    path('api/fcm-token/', views.update_fcm_token, name='update_fcm_token'),
    path('api/calls/initiate/', views.initiate_call, name='initiate_call'),
    path('api/calls/<int:call_id>/status/', views.update_call_status, name='update_call_status'),
    path('api/calls/history/', views.get_call_history, name='get_call_history'),
    
    # Agent URLs
    path('api/agent/dashboard/', views.agent_dashboard, name='agent_dashboard'),
    path('api/agent/wallet/', views.agent_wallet, name='agent_wallet'),
    path('api/agent/withdraw/', views.request_withdrawal, name='request_withdrawal'),
]
