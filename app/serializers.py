from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Profile, Offer, TermsAndConditions, PrivacyPolicy, HelpLine, UserActivity, CallHistory

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone_number', 'is_online', 'is_on_call', 'coins', 'created_at']
        read_only_fields = ['id', 'created_at', 'is_online', 'is_on_call', 'coins']

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Profile
        fields = ['id', 'user', 'name', 'age', 'gender', 'phone_number', 'bio', 'profile_picture', 'is_verified', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_verified']

class ProfileCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['name', 'age', 'gender', 'phone_number', 'bio', 'profile_picture']

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    profile = ProfileCreateSerializer(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'password', 'profile']
    
    def create(self, validated_data):
        profile_data = validated_data.pop('profile')
        password = validated_data.pop('password')
        
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        
        Profile.objects.create(user=user, **profile_data)
        return user

class GoogleAuthSerializer(serializers.Serializer):
    google_id = serializers.CharField()
    email = serializers.EmailField()
    name = serializers.CharField()
    profile_picture = serializers.URLField(required=False)

class PhoneAuthSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    otp = serializers.CharField()

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
        else:
            raise serializers.ValidationError('Username and password are required')
            
        attrs['user'] = user
        return attrs

class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = ['id', 'title', 'description', 'coin_value', 'is_active', 'start_date', 'end_date', 'created_at']

class TermsAndConditionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TermsAndConditions
        fields = ['id', 'title', 'content', 'is_active', 'created_at', 'updated_at']

class PrivacyPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivacyPolicy
        fields = ['id', 'title', 'content', 'is_active', 'created_at', 'updated_at']

class HelpLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = HelpLine
        fields = ['id', 'title', 'phone_number', 'email', 'address', 'is_active', 'created_at', 'updated_at']

class UserActivitySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserActivity
        fields = ['id', 'user', 'activity_type', 'timestamp']
        read_only_fields = ['id', 'timestamp']

class OnlineUserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'profile', 'is_online', 'coins']

class OnCallUserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'profile', 'is_on_call', 'coins']

class CallHistorySerializer(serializers.ModelSerializer):
    caller = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)

    class Meta:
        model = CallHistory
        fields = ['id', 'caller', 'receiver', 'channel_name', 'call_type', 'status', 'start_time', 'end_time']
        read_only_fields = ['id', 'caller', 'receiver', 'channel_name', 'start_time']