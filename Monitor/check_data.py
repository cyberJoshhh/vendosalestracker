#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Monitor.settings')
django.setup()

from monitor_app.models import SalesRecord, WifiVendo
from django.db.models import Sum
from datetime import datetime
from django.utils import timezone

print("=== Sales Records ===")
for record in SalesRecord.objects.all():
    print(f"- {record.wifi_vendo.name}: ₱{record.overall_profit} on {record.date} (year: {record.date.year}, month: {record.date.month})")

print(f"\n=== Total Sales ===")
total = SalesRecord.objects.aggregate(total=Sum('overall_profit'))['total'] or 0
print(f"Total: ₱{total}")

print(f"\n=== WiFi Vendos ===")
for vendo in WifiVendo.objects.all():
    print(f"- {vendo.name} ({vendo.status})")

print(f"\n=== Current Year ===")
current_year = timezone.now().year
print(f"Current year: {current_year}")

print(f"\n=== Sales by Month (Current Year) ===")
for month in range(1, 13):
    month_sales = SalesRecord.objects.filter(
        date__year=current_year,
        date__month=month
    ).aggregate(total=Sum('overall_profit'))['total'] or 0
    month_name = datetime(current_year, month, 1).strftime('%B')
    print(f"- {month_name}: ₱{month_sales}")

print(f"\n=== All Years in Database ===")
years = SalesRecord.objects.dates('date', 'year')
for year in years:
    print(f"- {year.year}")

print(f"\n=== Sales by Month (2025) ===")
for month in range(1, 13):
    month_sales = SalesRecord.objects.filter(
        date__year=2025,
        date__month=month
    ).aggregate(total=Sum('overall_profit'))['total'] or 0
    month_name = datetime(2025, month, 1).strftime('%B')
    print(f"- {month_name}: ₱{month_sales}") 