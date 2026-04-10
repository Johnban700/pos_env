from django.urls import path
from . import views

app_name = 'pos'

urlpatterns = [
    path('', views.pos_terminal, name='terminal'),
    path('complete-sale/', views.complete_sale, name='complete_sale'),
    path('receipt/<int:sale_id>/', views.receipt_view, name='receipt'),
    path('start-shift/', views.start_shift, name='start_shift'),
    path('end-shift/', views.end_shift, name='end_shift'),
]