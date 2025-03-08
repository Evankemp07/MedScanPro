from django.contrib import admin
from django.utils.html import mark_safe
from .models import ScanRecord

@admin.register(ScanRecord)
class ScanRecordAdmin(admin.ModelAdmin):
    list_display = ('barcode', 'brand_name', 'company_name', 'scan_time', 'count', 'is_manual_entry', 'item_name', 'has_image', 'image_preview')  
    list_filter = ('scan_time', 'is_manual_entry', ('image', admin.EmptyFieldListFilter))  
    search_fields = ('barcode', 'brand_name', 'company_name', 'item_name')  
    readonly_fields = ('scan_time',)  
    ordering = ('-scan_time',)  

    fieldsets = (
        ("Scan Details", {
            "fields": ("barcode", "brand_name", "company_name", "scan_time", "count", "is_manual_entry"),
        }),
        ("Item Details", {
            "fields": ("device_description", "item_description", "expiration_date", "version_model_number", "item_name", "labeled_contains_nrl"),
        }),
        ("Image Upload", {
            "fields": ("image",),
        }),
    )

    def has_image(self, obj):
        """Returns True/False if an image is uploaded."""
        return bool(obj.image)
    has_image.boolean = True
    has_image.short_description = "Has Image"

    def image_preview(self, obj):
        """Show image preview in admin panel if available."""
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="75" height="75" style="border-radius:5px"/>')
        return "No Image"
    
    image_preview.short_description = "Preview"

