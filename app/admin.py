from django.contrib import admin
from .models import User, Profile, Offer, UserActivity, CallHistory

admin.site.register(User)
admin.site.register(Profile)
admin.site.register(Offer)
admin.site.register(UserActivity)
admin.site.register(CallHistory)
