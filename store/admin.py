from django.contrib import admin
from .models import Category, SourceCode, Purchase

# Register your models here.

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(SourceCode)
class SourceCodeAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'price', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('title', 'description', 'features', 'technologies')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('customer_email', 'source_code', 'purchase_date', 'download_count', 'is_active')
    list_filter = ('is_active', 'purchase_date')
    search_fields = ('customer_email', 'shopify_order_id')
    readonly_fields = ('purchase_date', 'download_count')
