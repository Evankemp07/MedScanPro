from django import forms
from .models import ScanRecord

class EditScanForm(forms.ModelForm):
    """Form to edit scan details."""
    class Meta:
        model = ScanRecord
        fields = [
            'barcode', 'brand_name', 'company_name', 'device_description',
            'item_description', 'expiration_date', 'version_model_number',
            'item_name', 'labeled_contains_nrl', 'image'
        ]
