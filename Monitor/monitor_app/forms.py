from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Collector, SalesRecord, WifiVendo
from django.utils import timezone
import pytz

class WifiVendoForm(forms.ModelForm):
    class Meta:
        model = WifiVendo
        fields = ['name', 'location', 'status']
        widgets = {
            'status': forms.Select(choices=WifiVendo.STATUS_CHOICES),
        }

class CollectorForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()
    address = forms.CharField(widget=forms.TextInput())

    class Meta:
        model = Collector
        fields = ['phone_number', 'address']

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords don't match")
        return confirm_password

    def save(self, commit=True):
        collector = super().save(commit=False)
        
        # Create the user account
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name']
        )
        
        collector.user = user
        
        if commit:
            collector.save()
        
        return collector

class SalesRecordForm(forms.ModelForm):
    # Add status field for updating WiFi vendo status
    vendo_status = forms.ChoiceField(
        choices=WifiVendo.STATUS_CHOICES,
        required=False,
        label='Update WiFi Vendo Status',
        help_text='Optional: Update the status of the selected WiFi vendo',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def get_philippine_time(self):
        """Get current time in Philippine timezone"""
        ph_tz = pytz.timezone('Asia/Manila')
        return timezone.now().astimezone(ph_tz)
    
    date = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={
                'type': 'datetime-local',
                'readonly': 'readonly'
            },
            format='%Y-%m-%dT%H:%M'
        ),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial value to current Philippine time
        ph_tz = pytz.timezone('Asia/Manila')
        ph_time = timezone.now().astimezone(ph_tz)
        self.fields['date'].initial = ph_time.strftime('%Y-%m-%dT%H:%M')
        
        # Set initial status to current vendo status if editing
        if self.instance and self.instance.pk and self.instance.wifi_vendo:
            self.fields['vendo_status'].initial = self.instance.wifi_vendo.status

    class Meta:
        model = SalesRecord
        fields = ['wifi_vendo', 'amount', 'share', 'overall_profit', 'report', 'date']
        labels = {
            'amount': 'Amount Collected',
            'report': 'Report / Notes',
        }
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'share': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'overall_profit': forms.NumberInput(attrs={
                'step': '0.01', 
                'min': '0', 
                'readonly': 'readonly',
                'style': 'background-color: #f8f9fa; cursor: not-allowed;'
            }),
            'report': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if not date:
            # Return current Philippine time if no date provided
            ph_tz = pytz.timezone('Asia/Manila')
            return timezone.now().astimezone(ph_tz)
        return date 