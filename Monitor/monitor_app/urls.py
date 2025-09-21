from django.urls import path
from . import views

app_name = 'monitor_app'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add-sales/', views.add_sales, name='add_sales'),
    path('sales-history/', views.sales_history, name='sales_history'),
    path('add-collector/', views.add_collector, name='add_collector'),
    path('add-vendo/', views.add_vendo, name='add_vendo'),
    path('reports/', views.reports, name='reports'),
    path('recent-sales/', views.recent_sales_view, name='recent_sales'),
    path('collectors/', views.collectors_list_view, name='collectors_list'),
    path('wifi-vendos/', views.wifi_vendos_list_view, name='wifi_vendos_list'),
    path('toggle-collector-status/', views.toggle_collector_status, name='toggle_collector_status'),
]