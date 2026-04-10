from django.contrib import admin
from django.utils.html import format_html
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Product, Sale, SaleItem, Category, CashierShift

class ProductResource(resources.ModelResource):
    class Meta:
        model = Product
        fields = ('barcode', 'name', 'price', 'stock', 'category__name')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):   # Changed from ImportExportModelAdmin
    list_display = ['name', 'barcode', 'price', 'stock', 'stock_status', 'low_stock_threshold']
    list_editable = ['price', 'stock']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'barcode']

    def stock_status(self, obj):
        if obj.stock <= obj.low_stock_threshold:
            return format_html('<span style="color:red; font-weight:bold;">{} (Low!)</span>', obj.stock)
        return obj.stock
    stock_status.short_description = 'Stock Status'
@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'cashier', 'date', 'total', 'payment_method']
    list_filter = ['date', 'payment_method', 'cashier']
    search_fields = ['transaction_id', 'cashier__username']
    readonly_fields = ['transaction_id', 'date', 'subtotal', 'tax_amount', 'total', 'change']
    date_hierarchy = 'date'

    def has_add_permission(self, request):
        return False  # Prevent manual creation of sales

@admin.register(CashierShift)
class CashierShiftAdmin(admin.ModelAdmin):
    list_display = ['cashier', 'start_time', 'end_time', 'total_sales']
    list_filter = ['cashier']

admin.site.register(Category)
admin.site.register(SaleItem)