from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Sum, Count, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import datetime, timedelta
import json
from .models import WifiVendo, Collector, SalesRecord
from .forms import SalesRecordForm, CollectorForm, WifiVendoForm
from django.db.models.functions import TruncMonth
from django.utils.timezone import localtime
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


def index(request):
    if request.user.is_authenticated:
        return redirect('monitor_app:dashboard')
    return redirect('monitor_app:login')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('monitor_app:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # ✅ Check if user is in 'collector' group and NOT superuser
            if user.groups.filter(name='collector').exists() and not user.is_superuser:
                return redirect('monitor_app:add_sales')  # Make sure this matches your URL name
            else:
                return redirect('monitor_app:dashboard')
        else:
            # Check if user exists but is disabled
            try:
                existing_user = User.objects.get(username=username)
                if not existing_user.is_active:
                    messages.error(request, 'Your account has been disabled. Please contact an administrator for assistance.')
                else:
                    messages.error(request, 'Invalid username or password.')
            except User.DoesNotExist:
                messages.error(request, 'Invalid username or password.')

    return render(request, 'monitor_app/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('monitor_app:login')

@login_required
def dashboard(request):
    # Get the collector associated with the logged-in user
    try:
        collector = Collector.objects.get(user=request.user)
        is_admin = False
    except Collector.DoesNotExist:
        collector = None
        is_admin = True

    # Get sales records based on user type
    if is_admin:
        sales_records = SalesRecord.objects.all().order_by('-date')
        collectors = Collector.objects.all().annotate(
            total_sales=Sum(Coalesce('salesrecord__amount', 0, output_field=DecimalField())),
            total_profit=Sum(Coalesce('salesrecord__overall_profit', 0, output_field=DecimalField()))
        )
        total_collectors = collectors.count()
        active_collectors = collectors.filter(user__is_active=True).count()
        
        # Get WiFi vendo statistics
        total_vendos = WifiVendo.objects.count()
        active_vendos = WifiVendo.objects.filter(status='active').count()
        wifi_vendos = WifiVendo.objects.all().annotate(
            total_sales=Sum(Coalesce('salesrecord__overall_profit', 0, output_field=DecimalField()))
        )
    else:
        sales_records = SalesRecord.objects.filter(collector=collector).order_by('-date')
        collectors = None
        total_collectors = None
        active_collectors = None
        total_vendos = None
        active_vendos = None
        wifi_vendos = None

    # Calculate total sales
    total_sales = sales_records.aggregate(total=Sum(Coalesce('overall_profit', 0, output_field=DecimalField())))['total'] or 0

    # Calculate today's sales - get the most recent sales date
    utc_now = timezone.now()
    utc_today = utc_now.date()
    
    # Get the most recent sales date from the database
    most_recent_record = sales_records.order_by('-date').first()
    if most_recent_record:
        most_recent_date = most_recent_record.date.date()
        print(f"DEBUG - Current UTC date: {utc_today}")
        print(f"DEBUG - Most recent sales date: {most_recent_date}")
        
        # Use the most recent sales date instead of today
        # Get latest sales using manual date comparison (most reliable)
        all_records = sales_records.all()
        latest_sales = 0
        for record in all_records:
            record_date = record.date.date()
            if record_date == most_recent_date:
                latest_sales += float(record.overall_profit or 0)
    else:
        latest_sales = 0
        print(f"DEBUG - No sales records found")
    


    # Calculate monthly sales for the chart (January to December of current year)
    monthly_sales = {}
    
    # Get all records for manual processing
    all_records = sales_records.all()
    
    # Get the year from the most recent record or current year
    if most_recent_record:
        target_year = most_recent_record.date.year
    else:
        target_year = utc_today.year
    
    print(f"DEBUG - Calculating monthly data for year: {target_year}")
    
    # Calculate sales for each month (January to December)
    for month_num in range(1, 13):
        # Get month name and year for label
        month_date = datetime(target_year, month_num, 1)
        month_label = month_date.strftime('%B %Y')
        
        # Calculate sales for this month using manual date comparison
        month_sales = 0
        for record in all_records:
            record_date = record.date.date()
            if record_date.year == target_year and record_date.month == month_num:
                month_sales += float(record.overall_profit or 0)
        
        monthly_sales[month_label] = month_sales
        
        # Debug output
        if month_sales > 0:
            print(f"DEBUG - {month_label}: ₱{month_sales}")
    
    print(f"DEBUG - Monthly sales data: {monthly_sales}")

    # Convert monthly_sales to JSON for safe template rendering
    monthly_sales_json = json.dumps(monthly_sales)
    


    context = {
        'collector': collector,
        'is_admin': is_admin,
        'total_sales': total_sales,
        'today_sales': latest_sales,  # This is actually latest sales, not today's
        'today_sales_date': most_recent_date if most_recent_record else None,
        'monthly_sales': monthly_sales,
        'monthly_sales_json': monthly_sales_json,
        'sales_records': sales_records[:15],  # Get the 15 most recent records
        'collectors': collectors,
        'total_collectors': total_collectors,
        'active_collectors': active_collectors,
        'total_vendos': total_vendos,
        'active_vendos': active_vendos,
        'wifi_vendos': wifi_vendos,
    }
    
    return render(request, 'monitor_app/dashboard.html', context)

@login_required
def add_wifi_vendo(request):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to add WiFi vendos.')
        return redirect('monitor_app:dashboard')
    
    if request.method == 'POST':
        form = WifiVendoForm(request.POST)
        if form.is_valid():
            try:
                wifi_vendo = form.save()
                messages.success(request, f'WiFi Vendo {wifi_vendo.name} has been added successfully.')
                return redirect('monitor_app:dashboard')
            except Exception as e:
                messages.error(request, f'Error creating WiFi vendo: {str(e)}')
    else:
        form = WifiVendoForm()
    
    return render(request, 'monitor_app/add_wifi_vendo.html', {'form': form})

@login_required
def add_collector(request):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to add collectors.')
        return redirect('monitor_app:dashboard')
    
    if request.method == 'POST':
        form = CollectorForm(request.POST)
        if form.is_valid():
            try:
                collector = form.save()
                messages.success(request, f'Collector {collector.user.get_full_name()} has been added successfully.')
                return redirect('monitor_app:dashboard')
            except Exception as e:
                messages.error(request, f'Error creating collector: {str(e)}')
    else:
        form = CollectorForm()
    
    return render(request, 'monitor_app/add_collector.html', {'form': form})

@login_required
def add_sales(request):
    try:
        collector = Collector.objects.get(user=request.user)
    except Collector.DoesNotExist:
        messages.error(request, 'You are not registered as a collector.')
        return redirect('monitor_app:login')
    
    if request.method == 'POST':
        form = SalesRecordForm(request.POST)
        if form.is_valid():
            sales_record = form.save(commit=False)
            sales_record.collector = collector
            sales_record.save()
            
            # Update WiFi vendo status if provided
            vendo_status = form.cleaned_data.get('vendo_status')
            if vendo_status and sales_record.wifi_vendo:
                sales_record.wifi_vendo.status = vendo_status
                sales_record.wifi_vendo.save()
                messages.success(request, f'Sales record added successfully. WiFi vendo status updated to {vendo_status}.')
            else:
                messages.success(request, 'Sales record added successfully.')
            
            return redirect('monitor_app:dashboard')
    else:
        form = SalesRecordForm()
    
    return render(request, 'monitor_app/add_sales.html', {'form': form})

@login_required
def sales_history(request):
    try:
        collector = Collector.objects.get(user=request.user)
        is_admin = False
    except Collector.DoesNotExist:
        collector = None
        is_admin = True
    
    if is_admin:
        sales_records = SalesRecord.objects.all().order_by('-date')
    else:
        sales_records = SalesRecord.objects.filter(collector=collector).order_by('-date')
    
    return render(request, 'monitor_app/sales_history.html', {
        'sales_records': sales_records,
        'is_admin': is_admin
    })

@login_required
def add_vendo(request):
    if not request.user.is_staff:
        messages.error(request, "Only admin users can add new vendos.")
        return redirect('monitor_app:dashboard')
        
    if request.method == 'POST':
        form = WifiVendoForm(request.POST)
        if form.is_valid():
            vendo = form.save()
            messages.success(request, f'WiFi Vendo "{vendo.name}" has been added successfully.')
            return redirect('monitor_app:dashboard')
    else:
        form = WifiVendoForm()
    
    return render(request, 'monitor_app/add_vendo.html', {
        'form': form,
        'title': 'Add New WiFi Vendo'
    })

@login_required
def reports(request):
    # Check if user is admin or collector
    try:
        collector = Collector.objects.get(user=request.user)
        is_admin = False
    except Collector.DoesNotExist:
        collector = None
        is_admin = True
    
    # Get filter parameters
    selected_vendo_id = request.GET.get('vendo_id')
    year = request.GET.get('year', timezone.now().year)
    
    try:
        year = int(year)
    except (ValueError, TypeError):
        year = timezone.now().year
    
    # Base queryset for sales records
    if is_admin:
        sales_queryset = SalesRecord.objects.all()
    else:
        sales_queryset = SalesRecord.objects.filter(collector=collector)

    # Filter by selected wifi vendo if specified
    if selected_vendo_id:
        try:
            selected_vendo_id = int(selected_vendo_id)
            sales_queryset = sales_queryset.filter(wifi_vendo_id=selected_vendo_id)
            print(f"DEBUG: Filtering by vendo ID {selected_vendo_id}")
            print(f"DEBUG: Sales queryset count after vendo filter: {sales_queryset.count()}")
        except (ValueError, TypeError):
            selected_vendo_id = None
    
    # Get monthly sales data for the specified year
    monthly_sales_data = []
    monthly_labels = []
    monthly_data_for_table = []
    
    print(f"DEBUG: Getting monthly data for year {year}")
    for month in range(1, 13):
        month_sales = 0
        for record in sales_queryset:
            record_date = localtime(record.date)
            if record_date.year == year and record_date.month == month:
                month_sales += float(record.overall_profit or 0)
        month_name = datetime(year, month, 1).strftime('%B')
        monthly_labels.append(month_name)
        monthly_sales_data.append(month_sales)
        monthly_data_for_table.append((month_name, month_sales))
        if month_sales > 0:
            print(f"DEBUG: {month_name}: ₱{month_sales}")
    
    print(f"DEBUG: Monthly labels: {monthly_labels}")
    print(f"DEBUG: Monthly sales data: {monthly_sales_data}")
    print(f"DEBUG: Total for year: ₱{sum(monthly_sales_data)}")
    
    # Get vendo-wise sales for the year (for admin)
    vendo_sales_data = {}
    vendo_labels = []
    vendo_sales_amounts = []

    if is_admin and not selected_vendo_id:

        base_admin_queryset = SalesRecord.objects.all()
        vendos = WifiVendo.objects.all()
        print(f"DEBUG: Getting vendo data for {vendos.count()} vendos")
        
        for vendo in vendos:
            vendo_sales = base_admin_queryset.filter(
                wifi_vendo=vendo,
                date__year=year
            ).aggregate(total=Sum('overall_profit'))['total'] or 0
            
            vendo_sales_data[vendo.name] = float(vendo_sales)
            vendo_labels.append(vendo.name)
            vendo_sales_amounts.append(float(vendo_sales))
            if vendo_sales > 0:
                print(f"DEBUG: {vendo.name}: ₱{vendo_sales}")
        
        print(f"DEBUG: Vendo labels: {vendo_labels}")
        print(f"DEBUG: Vendo amounts: {vendo_sales_amounts}")
    
    # Get all wifi vendos for the filter dropdown
    all_vendos = WifiVendo.objects.all().order_by('name')
    
    # Get selected vendo details
    selected_vendo = None
    if selected_vendo_id:
        try:
            selected_vendo = WifiVendo.objects.get(id=selected_vendo_id)
        except WifiVendo.DoesNotExist:
            pass
    
    # Calculate totals
    total_sales_year = sales_queryset.filter(date__year=year).aggregate(total=Sum('overall_profit'))['total'] or 0
    total_transactions = sales_queryset.filter(date__year=year).count()
    
    # Get year range for dropdown
    earliest_sale = SalesRecord.objects.order_by('date').first()
    current_year = timezone.now().year
    if earliest_sale:
        start_year = earliest_sale.date.year
    else:
        start_year = current_year
    
    year_range = list(range(start_year, current_year + 1))
    year_range.reverse()
    
    # Debug output
    print(f"DEBUG: Context data being passed to template:")
    print(f"DEBUG: monthly_labels: {monthly_labels}")
    print(f"DEBUG: monthly_sales_data: {monthly_sales_data}")
    print(f"DEBUG: total_sales_year: {total_sales_year}")
    print(f"DEBUG: is_admin: {is_admin}")
    print(f"DEBUG: selected_vendo_id: {selected_vendo_id}")
    
    context = {
        'is_admin': is_admin,
        'collector': collector,
        'selected_year': year,
        'selected_vendo_id': selected_vendo_id,
        'selected_vendo': selected_vendo,
        'all_vendos': all_vendos,
        'year_range': year_range,
        
        # Chart data
        'monthly_labels': monthly_labels,
        'monthly_sales_data': monthly_sales_data,
        'monthly_data_for_table': monthly_data_for_table,
        'vendo_labels': vendo_labels,
        'vendo_sales_amounts': vendo_sales_amounts,
        
        # Summary data
        'total_sales_year': total_sales_year,
        'total_transactions': total_transactions,
        
        # Top performing data
        'top_month': monthly_labels[monthly_sales_data.index(max(monthly_sales_data))] if monthly_sales_data and max(monthly_sales_data) > 0 else 'N/A',
        'top_month_amount': max(monthly_sales_data) if monthly_sales_data else 0,
    }
    
    return render(request, 'monitor_app/reports.html', context)

@login_required
def recent_sales_view(request):
    sales_records = SalesRecord.objects.all().order_by('-date')[:50] # Limit to 50 recent sales
    return render(request, 'monitor_app/recent_sales.html', {'sales_records': sales_records})

@login_required
def collectors_list_view(request):
    collectors = Collector.objects.all().annotate(
        total_sales=Sum(Coalesce('salesrecord__amount', 0, output_field=DecimalField()))
    )
    return render(request, 'monitor_app/collectors_list.html', {'collectors': collectors})

@login_required
def wifi_vendos_list_view(request):
    wifi_vendos = WifiVendo.objects.all().annotate(
        total_sales=Sum(Coalesce('salesrecord__overall_profit', 0, output_field=DecimalField()))
    )
    return render(request, 'monitor_app/wifi_vendos_list.html', {'wifi_vendos': wifi_vendos})

@login_required
@require_http_methods(["POST"])
def toggle_collector_status(request):
    """
    Toggle collector status (enable/disable login)
    Only staff users can perform this action
    """
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'You do not have permission to perform this action.'}, status=403)
    
    try:
        data = json.loads(request.body)
        collector_id = data.get('collector_id')
        action = data.get('action')
        
        if not collector_id or not action:
            return JsonResponse({'success': False, 'message': 'Missing required parameters.'}, status=400)
        
        if action not in ['enable', 'disable']:
            return JsonResponse({'success': False, 'message': 'Invalid action. Must be "enable" or "disable".'}, status=400)
        
        try:
            collector = Collector.objects.get(id=collector_id)
        except Collector.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Collector not found.'}, status=404)
        
        # Update the user's is_active status
        if action == 'disable':
            collector.user.is_active = False
            message = f'Collector {collector.user.get_full_name()} has been disabled.'
        else:  # enable
            collector.user.is_active = True
            message = f'Collector {collector.user.get_full_name()} has been enabled.'
        
        collector.user.save()
        
        return JsonResponse({'success': True, 'message': message})
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'}, status=500)
