from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('add/', views.add_item_view, name='add_item'),
    path('calculate/', views.calculate_view, name='calculate'),
    path('edit/<int:pk>/', views.edit_item_view, name='edit_item'),
    path('send-whatsapp/', views.send_whatsapp_view, name='send_whatsapp'),
    path('orders/', views.orders_list_view, name='orders_list'),
    path('orders/json/', views.orders_json_view, name='orders_json'),
    path('orders/save/', views.save_order_view, name='save_order'),
    path('orders/pay/<str:order_id>/', views.pay_order_view, name='pay_order'),
]
