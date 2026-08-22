from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# Create your models here.

class User(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True, blank=True, null=True)
    google_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    is_online = models.BooleanField(default=False)
    is_on_call = models.BooleanField(default=False)
    coins = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    fcm_token = models.CharField(max_length=255, blank=True, null=True)
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['phone_number']
    
    def __str__(self):
        return self.username

class Profile(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    phone_number = models.CharField(max_length=15)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name}'s Profile"

class Offer(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    coin_value = models.IntegerField()
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.title

class TermsAndConditions(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

class PrivacyPolicy(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

class HelpLine(models.Model):
    title = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=50)  # 'login', 'logout', 'call_start', 'call_end'
    timestamp = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.user.username} - {self.activity_type}"

class CallHistory(models.Model):
    CALL_TYPES = [
        ('audio', 'Audio'),
        ('video', 'Video'),
    ]
    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('missed', 'Missed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    caller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='outgoing_calls')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incoming_calls')
    channel_name = models.CharField(max_length=100, unique=True)
    call_type = models.CharField(max_length=10, choices=CALL_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initiated')
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Call: {self.caller.username} -> {self.receiver.username} ({self.status})"

class AgentTaskConfig(models.Model):
    daily_call_target = models.PositiveIntegerField(default=50)
    weekly_call_target = models.PositiveIntegerField(default=250)
    monthly_call_target = models.PositiveIntegerField(default=1000)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.pk = 1 # Force it to be a singleton
        super(AgentTaskConfig, self).save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

class GlobalSetting(models.Model):
    TYPE_CHOICES = [
        ('int', 'Integer'),
        ('float', 'Float'),
        ('bool', 'Boolean'),
        ('str', 'String'),
    ]
    key = models.CharField(max_length=50, unique=True)
    value = models.CharField(max_length=255)
    data_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='str')
    description = models.TextField(blank=True, null=True)

    def get_typed_value(self):
        if self.data_type == 'int':
            return int(self.value)
        elif self.data_type == 'float':
            return float(self.value)
        elif self.data_type == 'bool':
            return str(self.value).lower() in ['true', '1', 't', 'y', 'yes']
        return str(self.value)
        
    def __str__(self):
        return f"{self.key}: {self.value} ({self.data_type})"

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Wallet - Balance: {self.balance}"

class WithdrawalRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='withdrawals')
    amount = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.agent.username} - {self.amount} ({self.status})"

class Transaction(models.Model):
    TYPE_CHOICES = [
        ('earn_call', 'Earned from Call'),
        ('withdrawal', 'Withdrawal'),
        ('coin_purchase', 'Coin Purchase'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    amount = models.IntegerField()
    transaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    reference_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.user.username} - {self.amount} ({self.transaction_type})"
