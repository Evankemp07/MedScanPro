from django.db import models
import os

class ScanRecord(models.Model):
    barcode = models.CharField(max_length=255, unique=False)
    brand_name = models.CharField(max_length=255, null=True, blank=True)
    company_name = models.CharField(max_length=255, null=True, blank=True)
    device_description = models.TextField(null=True, blank=True)
    item_description = models.TextField(null=True, blank=True)
    expiration_date = models.CharField(max_length=50, null=True, blank=True)
    version_model_number = models.CharField(max_length=255, null=True, blank=True)
    item_name = models.CharField(max_length=255, null=True, blank=True)
    labeled_contains_nrl = models.CharField(max_length=255, null=True, blank=True)
    scan_time = models.DateTimeField(auto_now_add=True)
    count = models.PositiveIntegerField(default=1)

    image = models.ImageField(upload_to='missing_scans/', null=True, blank=True)
    is_manual_entry = models.BooleanField(default=False)

    def image_filename(self):
        """Return the expected image filename based on barcode."""
        if self.image:
            return os.path.basename(self.image.name)
        return None

    def __str__(self):
        return f"Scan {self.barcode} - {self.brand_name if self.brand_name else 'Manual Entry'}"


class ScanHistory(models.Model):
    barcode = models.CharField(max_length=255)
    scan_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.barcode