from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils.html import format_html
from .models import WifiVendo, Collector, SalesRecord

class CollectorUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

@admin.register(Collector)
class CollectorAdmin(admin.ModelAdmin):
    form = CollectorUserCreationForm
    list_display = ('user', 'phone_number', 'address', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone_number')
    ordering = ('-created_at',)
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only create user if this is a new collector
            # Create the user
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email']
            )
            obj.user = user
        super().save_model(request, obj, form, change)

@admin.register(WifiVendo)
class WifiVendoAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'location')
    ordering = ('-created_at',)

@admin.register(SalesRecord)
class SalesRecordAdmin(admin.ModelAdmin):
    list_display = ('wifi_vendo', 'collector', 'amount', 'date', 'created_at')
    list_filter = ('date', 'wifi_vendo', 'collector')
    search_fields = ('wifi_vendo__name', 'collector__user__username')
    ordering = ('-date',)
