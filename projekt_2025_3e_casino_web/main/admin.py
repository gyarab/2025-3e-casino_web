from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'

# Re-register UserAdmin with the inline
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
UserAdmin.inlines = (UserProfileInline,)

admin.site.register(UserProfile)
