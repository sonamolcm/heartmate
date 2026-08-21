from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from django.utils import timezone
from .models import User, Profile, Offer, TermsAndConditions, PrivacyPolicy, HelpLine, UserActivity, CallHistory
from .serializers import (
    UserSerializer, ProfileSerializer, UserRegistrationSerializer,
    GoogleAuthSerializer, PhoneAuthSerializer, LoginSerializer,
    OfferSerializer, TermsAndConditionsSerializer, PrivacyPolicySerializer,
    HelpLineSerializer, OnlineUserSerializer, OnCallUserSerializer, CallHistorySerializer
)
import uuid
from django.conf import settings
from django.db.models import Q
try:
    from firebase_admin import messaging
except ImportError:
    pass
try:
    from agora_token_builder import RtcTokenBuilder
except ImportError:
    pass

# Create your views here.

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """Register a new user with profile creation"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        
        # Check for fcm_token
        fcm_token = request.data.get('fcm_token')
        if fcm_token:
            user.fcm_token = fcm_token
            user.save()
        
        # Log user activity
        UserActivity.objects.create(user=user, activity_type='registration')
        
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def google_auth(request):
    """Authenticate user with Google"""
    serializer = GoogleAuthSerializer(data=request.data)
    if serializer.is_valid():
        google_id = serializer.validated_data['google_id']
        email = serializer.validated_data['email']
        name = serializer.validated_data['name']
        
        # Check if user exists
        try:
            user = User.objects.get(google_id=google_id)
        except User.DoesNotExist:
            # Create new user
            user = User.objects.create(
                username=email.split('@')[0],
                email=email,
                google_id=google_id
            )
            # Create profile
            Profile.objects.create(
                user=user,
                name=name,
                age=18,  # Default age
                gender='other',  # Default gender
                phone_number=''  # Will be updated later
            )
            
            UserActivity.objects.create(user=user, activity_type='google_registration')
        
        # Check for fcm_token
        fcm_token = request.data.get('fcm_token')
        if fcm_token:
            user.fcm_token = fcm_token
        
        # Login user
        login(request, user)
        token, created = Token.objects.get_or_create(user=user)
        
        UserActivity.objects.create(user=user, activity_type='login')
        user.is_online = True
        user.save()
        
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
            'message': 'Google authentication successful'
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def phone_auth(request):
    """Authenticate user with phone number and OTP"""
    serializer = PhoneAuthSerializer(data=request.data)
    if serializer.is_valid():
        phone_number = serializer.validated_data['phone_number']
        otp = serializer.validated_data['otp']
        
        # Here you would verify the OTP (implement your OTP verification logic)
        # For demo purposes, we'll assume OTP is always valid
        
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response({
                'error': 'User not found with this phone number. Please register first.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check for fcm_token
        fcm_token = request.data.get('fcm_token')
        if fcm_token:
            user.fcm_token = fcm_token
        
        # Login user
        login(request, user)
        token, created = Token.objects.get_or_create(user=user)
        
        UserActivity.objects.create(user=user, activity_type='login')
        user.is_online = True
        user.save()
        
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
            'message': 'Phone authentication successful'
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def user_login(request):
    """Traditional username/password login"""
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        login(request, user)
        token, created = Token.objects.get_or_create(user=user)
        
        # Check for fcm_token
        fcm_token = request.data.get('fcm_token')
        if fcm_token:
            user.fcm_token = fcm_token
            
        UserActivity.objects.create(user=user, activity_type='login')
        user.is_online = True
        user.save()
        
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
            'message': 'Login successful'
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def user_logout(request):
    """Logout user and invalidate token"""
    try:
        request.user.auth_token.delete()
    except:
        pass
    
    UserActivity.objects.create(user=request.user, activity_type='logout')
    request.user.is_online = False
    request.user.is_on_call = False
    request.user.save()
    
    logout(request)
    
    return Response({
        'message': 'Logout successful'
    }, status=status.HTTP_200_OK)

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Get or update user profile"""
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        return Response({
            'error': 'Profile not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        from .serializers import ProfileCreateSerializer
        serializer = ProfileCreateSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Profile updated successfully',
                'profile': ProfileSerializer(profile).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request, user_id):
    """Get another user's profile"""
    try:
        user = User.objects.get(id=user_id)
        profile = user.profile
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)
    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Profile.DoesNotExist:
        return Response({
            'error': 'Profile not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_user_status(request):
    """Update user online/on-call status"""
    status_type = request.data.get('status_type')
    is_active = request.data.get('is_active', True)
    
    if status_type == 'online':
        request.user.is_online = is_active
    elif status_type == 'on_call':
        request.user.is_on_call = is_active
        if is_active:
            UserActivity.objects.create(user=request.user, activity_type='call_start')
        else:
            UserActivity.objects.create(user=request.user, activity_type='call_end')
    else:
        return Response({
            'error': 'Invalid status type. Use "online" or "on_call"'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    request.user.save()
    
    return Response({
        'message': f'Status updated: {status_type} = {is_active}',
        'user': UserSerializer(request.user).data
    })

# Menu Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def menu_items(request):
    """Get all menu items for the app"""
    menu_data = {
        'profile': {
            'title': 'My Profile',
            'endpoint': '/api/profile/'
        },
        'terms_conditions': {
            'title': 'Terms & Conditions',
            'endpoint': '/api/terms-conditions/'
        },
        'privacy_policy': {
            'title': 'Privacy Policy',
            'endpoint': '/api/privacy-policy/'
        },
        'help_line': {
            'title': 'Help Line',
            'endpoint': '/api/help-line/'
        },
        'logout': {
            'title': 'Logout',
            'endpoint': '/api/logout/'
        }
    }
    
    return Response(menu_data)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_terms_conditions(request):
    """Get active terms and conditions"""
    terms = TermsAndConditions.objects.filter(is_active=True).order_by('-created_at')
    if terms.exists():
        serializer = TermsAndConditionsSerializer(terms.first())
        return Response(serializer.data)
    return Response({
        'error': 'No active terms and conditions found'
    }, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_privacy_policy(request):
    """Get active privacy policy"""
    policies = PrivacyPolicy.objects.filter(is_active=True).order_by('-created_at')
    if policies.exists():
        serializer = PrivacyPolicySerializer(policies.first())
        return Response(serializer.data)
    return Response({
        'error': 'No active privacy policy found'
    }, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_help_line(request):
    """Get active help line information"""
    help_lines = HelpLine.objects.filter(is_active=True).order_by('-created_at')
    if help_lines.exists():
        serializer = HelpLineSerializer(help_lines.first())
        return Response(serializer.data)
    return Response({
        'error': 'No active help line found'
    }, status=status.HTTP_404_NOT_FOUND)

# User Listing Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_online_users(request):
    """Get list of online users"""
    online_users = User.objects.filter(is_online=True).exclude(id=request.user.id)
    serializer = OnlineUserSerializer(online_users, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_on_call_users(request):
    """Get list of users currently on call"""
    on_call_users = User.objects.filter(is_on_call=True).exclude(id=request.user.id)
    serializer = OnCallUserSerializer(on_call_users, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_users(request):
    """Get list of all users (with pagination)"""
    users = User.objects.exclude(id=request.user.id).select_related('profile')
    
    # Simple pagination
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    start = (page - 1) * page_size
    end = start + page_size
    
    paginated_users = users[start:end]
    serializer = OnlineUserSerializer(paginated_users, many=True)
    
    return Response({
        'users': serializer.data,
        'total': users.count(),
        'page': page,
        'page_size': page_size
    })

# Coin and Offers Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_coins(request):
    """Get current user's coin balance"""
    return Response({
        'coins': request.user.coins,
        'user_id': request.user.id
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_coins(request):
    """Add coins to user account (admin only in real app)"""
    coins_to_add = request.data.get('coins', 0)
    
    if not isinstance(coins_to_add, int) or coins_to_add <= 0:
        return Response({
            'error': 'Please provide a valid positive number of coins'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    request.user.coins += coins_to_add
    request.user.save()
    
    # Log the transaction
    UserActivity.objects.create(
        user=request.user, 
        activity_type=f'coins_added_{coins_to_add}'
    )
    
    return Response({
        'message': f'{coins_to_add} coins added successfully',
        'new_balance': request.user.coins
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deduct_coins(request):
    """Deduct coins from user account"""
    coins_to_deduct = request.data.get('coins', 0)
    
    if not isinstance(coins_to_deduct, int) or coins_to_deduct <= 0:
        return Response({
            'error': 'Please provide a valid positive number of coins'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if request.user.coins < coins_to_deduct:
        return Response({
            'error': 'Insufficient coins balance'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    request.user.coins -= coins_to_deduct
    request.user.save()
    
    # Log the transaction
    UserActivity.objects.create(
        user=request.user, 
        activity_type=f'coins_deducted_{coins_to_deduct}'
    )
    
    return Response({
        'message': f'{coins_to_deduct} coins deducted successfully',
        'new_balance': request.user.coins
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def get_active_offers(request):
    """Get all active offers"""
    from django.utils import timezone
    
    active_offers = Offer.objects.filter(
        is_active=True,
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    ).order_by('-created_at')
    
    serializer = OfferSerializer(active_offers, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_offer_detail(request, offer_id):
    """Get details of a specific offer"""
    try:
        offer = Offer.objects.get(id=offer_id, is_active=True)
        serializer = OfferSerializer(offer)
        return Response(serializer.data)
    except Offer.DoesNotExist:
        return Response({
            'error': 'Offer not found or inactive'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def redeem_offer(request, offer_id):
    """Redeem an offer (add coins to user)"""
    try:
        offer = Offer.objects.get(id=offer_id, is_active=True)
        
        # Check if offer is still valid
        from django.utils import timezone
        if timezone.now() < offer.start_date or timezone.now() > offer.end_date:
            return Response({
                'error': 'Offer is not currently active'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Add coins to user
        request.user.coins += offer.coin_value
        request.user.save()
        
        # Log the transaction
        UserActivity.objects.create(
            user=request.user, 
            activity_type=f'offer_redeemed_{offer.id}'
        )
        
        return Response({
            'message': f'Offer redeemed successfully! {offer.coin_value} coins added',
            'new_balance': request.user.coins,
            'offer': OfferSerializer(offer).data
        })
        
    except Offer.DoesNotExist:
        return Response({
            'error': 'Offer not found or inactive'
        }, status=status.HTTP_404_NOT_FOUND)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_coins(request):
    """Add coins to user account"""
    coins_to_add = request.data.get('coins', 0)
    
    if not isinstance(coins_to_add, int) or coins_to_add <= 0:
        return Response({
            'error': 'Please provide a valid positive number of coins'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    request.user.coins += coins_to_add
    request.user.save()
    
    # Log the transaction
    UserActivity.objects.create(
        user=request.user, 
        activity_type=f'coins_added_{coins_to_add}'
    )
    
    return Response({
        'message': f'{coins_to_add} coins added successfully',
        'new_balance': request.user.coins
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deduct_coins(request):
    """Deduct coins from user account"""
    coins_to_deduct = request.data.get('coins', 0)
    
    if not isinstance(coins_to_deduct, int) or coins_to_deduct <= 0:
        return Response({
            'error': 'Please provide a valid positive number of coins'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if request.user.coins < coins_to_deduct:
        return Response({
            'error': 'Insufficient coins balance'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    request.user.coins -= coins_to_deduct
    request.user.save()
    
    # Log the transaction
    UserActivity.objects.create(
        user=request.user, 
        activity_type=f'coins_deducted_{coins_to_deduct}'
    )
    
    return Response({
        'message': f'{coins_to_deduct} coins deducted successfully',
        'new_balance': request.user.coins
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def get_active_offers(request):
    """Get all active offers"""
    from django.utils import timezone
    
    active_offers = Offer.objects.filter(
        is_active=True,
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    ).order_by('-created_at')
    
    serializer = OfferSerializer(active_offers, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_offer_detail(request, offer_id):
    """Get details of a specific offer"""
    try:
        offer = Offer.objects.get(id=offer_id, is_active=True)
        serializer = OfferSerializer(offer)
        return Response(serializer.data)
    except Offer.DoesNotExist:
        return Response({
            'error': 'Offer not found or inactive'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def redeem_offer(request, offer_id):
    """Redeem an offer (add coins to user)"""
    try:
        offer = Offer.objects.get(id=offer_id, is_active=True)
        
        # Check if offer is still valid
        from django.utils import timezone
        if timezone.now() < offer.start_date or timezone.now() > offer.end_date:
            return Response({
                'error': 'Offer is not currently active'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Add coins to user
        request.user.coins += offer.coin_value
        request.user.save()
        
        # Log the transaction
        UserActivity.objects.create(
            user=request.user, 
            activity_type=f'offer_redeemed_{offer.id}'
        )
        
        return Response({
            'message': f'Offer redeemed successfully! {offer.coin_value} coins added',
            'new_balance': request.user.coins,
            'offer': OfferSerializer(offer).data
        })
        
    except Offer.DoesNotExist:
        return Response({
            'error': 'Offer not found or inactive'
        }, status=status.HTTP_404_NOT_FOUND)

# -----------------------------------------------------------------------------
# FCM & Calling APIs
# -----------------------------------------------------------------------------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_fcm_token(request):
    fcm_token = request.data.get('fcm_token')
    if not fcm_token:
        return Response({'error': 'fcm_token is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    request.user.fcm_token = fcm_token
    request.user.save()
    return Response({'message': 'FCM token updated successfully'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_call(request):
    receiver_id = request.data.get('receiver_id')
    call_type = request.data.get('call_type', 'video')
    
    if not receiver_id:
        return Response({'error': 'receiver_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        receiver = User.objects.get(id=receiver_id)
    except User.DoesNotExist:
        return Response({'error': 'Receiver not found'}, status=status.HTTP_404_NOT_FOUND)
        
    # Generate unique channel name
    channel_name = str(uuid.uuid4())
    
    # Create CallHistory record
    call = CallHistory.objects.create(
        caller=request.user,
        receiver=receiver,
        channel_name=channel_name,
        call_type=call_type,
        status='initiated'
    )
    
    # Generate Agora Token
    app_id = getattr(settings, 'AGORA_APP_ID', '')
    app_certificate = getattr(settings, 'AGORA_APP_CERTIFICATE', '')
    
    # Role: 1 = Publisher, 2 = Subscriber
    role = 1 
    # Token expiration (24 hours)
    expiration_time_in_seconds = 3600 * 24
    current_timestamp = int(timezone.now().timestamp())
    privilege_expired_ts = current_timestamp + expiration_time_in_seconds
    
    token = ""
    try:
        if 'RtcTokenBuilder' in globals():
            token = RtcTokenBuilder.buildTokenWithUid(
                app_id, app_certificate, channel_name, request.user.id, role, privilege_expired_ts
            )
    except Exception as e:
        return Response({'error': f'Failed to generate token: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    # Send FCM Notification to Receiver
    if receiver.fcm_token and 'messaging' in globals():
        try:
            message = messaging.Message(
                data={
                    'type': 'incoming_call',
                    'call_id': str(call.id),
                    'channel_name': channel_name,
                    'caller_id': str(request.user.id),
                    'caller_name': request.user.username,
                    'call_type': call_type
                },
                token=receiver.fcm_token
            )
            messaging.send(message)
        except Exception as e:
            print(f"Failed to send FCM: {e}")
            
    return Response({
        'call_id': call.id,
        'channel_name': channel_name,
        'token': token,
        'uid': request.user.id
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_call_status(request, call_id):
    new_status = request.data.get('status')
    
    valid_statuses = [c[0] for c in CallHistory.STATUS_CHOICES]
    if new_status not in valid_statuses:
        return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        call = CallHistory.objects.get(id=call_id)
    except CallHistory.DoesNotExist:
        return Response({'error': 'Call not found'}, status=status.HTTP_404_NOT_FOUND)
        
    # Security: only caller or receiver can update
    if request.user != call.caller and request.user != call.receiver:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        
    call.status = new_status
    if new_status == 'completed':
        call.end_time = timezone.now()
        
    call.save()
    
    response_data = {'message': f'Call status updated to {new_status}'}
    
    # If accepted, generate a token for the receiver to join
    if new_status == 'accepted':
        app_id = getattr(settings, 'AGORA_APP_ID', '')
        app_certificate = getattr(settings, 'AGORA_APP_CERTIFICATE', '')
        role = 1 # Publisher
        expiration_time_in_seconds = 3600 * 24
        privilege_expired_ts = int(timezone.now().timestamp()) + expiration_time_in_seconds
        
        try:
            if 'RtcTokenBuilder' in globals():
                token = RtcTokenBuilder.buildTokenWithUid(
                    app_id, app_certificate, call.channel_name, request.user.id, role, privilege_expired_ts
                )
                response_data['token'] = token
                response_data['channel_name'] = call.channel_name
                response_data['uid'] = request.user.id
        except Exception as e:
            print(f"Failed to generate receiver token: {e}")
            
    return Response(response_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_call_history(request):
    # Get calls where user is either caller or receiver
    calls = CallHistory.objects.filter(
        Q(caller=request.user) | Q(receiver=request.user)
    ).order_by('-start_time')
    
    serializer = CallHistorySerializer(calls, many=True)
    return Response(serializer.data)
