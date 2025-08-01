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
]