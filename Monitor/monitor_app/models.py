from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

class WifiVendo(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('maintenance', 'Maintenance'),
        ('inactive', 'Inactive'),
    ]
    
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.location} ({self.get_status_display()})"

class Collector(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    phone_number = models.CharField(max_length=20)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user:
            return f"{self.user.get_full_name()}"
        return f"Collector {self.id}"

class SalesRecord(models.Model):
    wifi_vendo = models.ForeignKey(WifiVendo, on_delete=models.CASCADE)
    collector = models.ForeignKey(Collector, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    share = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    overall_profit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    report = models.TextField(null=True, blank=True, help_text="Optional report or notes about this sales record")
    date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.wifi_vendo.name} - {self.amount} - {self.date}"
