import csv
from medscanpro.models import ScanRecord
from datetime import datetime

# Define CSV filename
csv_filename = "recovered_data.csv"

# Fetch all existing records
data = ScanRecord.objects.all().values()

# Open CSV file and write data
with open(csv_filename, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)

    # Write CSV header
    writer.writerow([
        "barcode", "brand_name", "company_name", "device_description",
        "item_description", "expiration_date", "version_model_number",
        "item_name", "labeled_contains_nrl", "scan_time", "count", "is_manual_entry"
    ])

    # Write rows
    for record in data:
        writer.writerow([
            record["barcode"],
            record["brand_name"] or "",
            record["company_name"] or "",
            record["device_description"] or "",
            record["item_description"] or "",
            record["expiration_date"] or "",
            record["version_model_number"] or "",
            record["item_name"] or "",
            record["labeled_contains_nrl"] or "",
            record["scan_time"].strftime("%Y-%m-%d %H:%M:%S") if record["scan_time"] else "",
            record["count"],
            record["is_manual_entry"]
        ])

print(f"✅ Data exported successfully to {csv_filename}!")
