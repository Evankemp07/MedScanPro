import os
import re
import json
import logging
import sqlite3
import datetime
import requests
import pandas as pd

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.timezone import localtime
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages

from .models import ScanRecord
from .forms import EditScanForm

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Global constants and variables
DB_FILE = r"G:\MedScan\MedScan\medscanpro\media\items.db"  # Ensure correct path format
DATABASE_PATH = r"G:\MedScan\MedScan\medscanpro\media\gudid_devices.db"
current_ngrok_url = None  # Store the latest URL globally (or save in the database)

# --- Utility Functions ---

def remove_suffix(value):
    """Removes /A or /B from the end of a string, ensuring value is a valid string."""
    if not isinstance(value, str):
        return value
    return re.sub(r'[/][AB]$', '', value)

def sanitize_filename(filename):
    """Removes invalid characters from a filename."""
    return re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', filename)

def extract_gs1_di(udi_string):
    """
    Extracts the Device Identifier (DI), which is the GTIN (01) in GS1 format.
    If the input is already a GTIN, it returns it as is.
    """
    if re.fullmatch(r"\d{14}", udi_string):
        return udi_string

    match = re.match(r"01(\d{14})", udi_string)
    if match:
        return match.group(1)

    return None

# --- Database Lookup Functions ---

def find_item_details(version_model_number, catalog_number=None):
    """
    Search for the Item Name and Item Description in SQLite using
    Item Model Number first, then Catalog Number.
    """
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            query = """
                SELECT `Item Name`, `Item Description`, `Trading Partner Name`
                FROM items 
                WHERE `TP Item Number` = ? 
                LIMIT 1
            """
            cursor.execute(query, (version_model_number,))
            result = cursor.fetchone()

            if not result and catalog_number:
                cursor.execute(query, (catalog_number,))
                result = cursor.fetchone()

            if result:
                logging.info(f"Found item: {result}")
                return {
                    "item_name": result[0],
                    "item_description": result[1],
                    "trading_partner_name": result[2]
                }

        logging.info(f"Item {version_model_number} not found in database.")
        return {
            "item_name": "Item not found",
            "item_description": "Description not available",
            "trading_partner_name": "Not Found"
        }

    except Exception as e:
        logging.error(f"Database error in find_item_details: {str(e)}")
        return {
            "item_name": "Database Error",
            "item_description": f"Error: {str(e)}",
            "trading_partner_name": "error"
        }

def lookup_local_db(di):
    """
    Searches the local gudid_devices.db for the given DI and ensures that
    catalogNumber is included in the returned data.
    """
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM devices WHERE PrimaryDI = ?", (di,))
        result = cursor.fetchone()

        if result:
            column_names = [desc[0] for desc in cursor.description]
            device_data = dict(zip(column_names, result))
            # Ensure catalogNumber is included
            device_data["catalogNumber"] = device_data.get("catalogNumber", "n/a")
            return device_data

    except Exception as e:
        logging.error(f"Database error: {e}")
        return {"Error": "Database lookup failed"}
    finally:
        conn.close()

    return None

# --- Django Views ---

def lookup_gudid(request):
    """
    Look up device information from the local DB first, then GUDID API if not found.
    """
    if request.method == 'POST':
        barcode = request.POST.get('barcode')
        count = request.POST.get('count', 1)

        if barcode:
            # Skip lookup for "Next Rack" barcodes
            if barcode.lower().startswith("hf"):
                brand_name = company_name = "Next Rack"
                device_description = "Storage Rack"
                version_model_number = catalog_number = "n/a"
                expiration_date = labeled_contains_nrl = "n/a"
                item_details = {
                    "item_description": "Storage Rack",
                    "item_name": "Next Rack"
                }
            else:
                di = extract_gs1_di(barcode)
                if not di:
                    return render(request, 'scanner.html', {'barcode_not_found': True, 'barcode': barcode})

                device_data = lookup_local_db(di)

                if not device_data:
                    api_url = f"https://accessgudid.nlm.nih.gov/api/v2/devices/lookup.json?udi={barcode}"
                    response = requests.get(api_url)
                    if response.status_code == 200:
                        device_data = response.json().get('gudid', {}).get('device', {})
                    else:
                        return render(request, 'scanner.html', {'barcode_not_found': True, 'barcode': barcode})

                version_model_number = remove_suffix(device_data.get('versionModelNumber', 'n/a'))
                catalog_number = remove_suffix(device_data.get('catalogNumber', 'n/a'))
                brand_name = device_data.get('brandName', 'n/a')
                company_name = device_data.get('companyName', 'n/a')
                device_description = device_data.get('deviceDescription', 'n/a')
                expiration_date = device_data.get('expirationDate', None)
                expiration_date = "True" if expiration_date == 1 else "False" if expiration_date is not None else "n/a"
                labeled_contains_nrl = device_data.get('labeledContainsNRL', None)
                labeled_contains_nrl = "True" if labeled_contains_nrl == 1 else "False" if labeled_contains_nrl is not None else "n/a"
                item_details = find_item_details(version_model_number, catalog_number)

            try:
                count = int(count)
            except ValueError:
                count = 1

            ScanRecord.objects.create(
                barcode=barcode,
                brand_name=brand_name,
                company_name=company_name,
                device_description=device_description,
                item_description=item_details["item_description"],
                expiration_date=expiration_date,
                version_model_number=version_model_number,
                item_name=item_details["item_name"],
                labeled_contains_nrl=labeled_contains_nrl,
                scan_time=datetime.datetime.now(),
                is_manual_entry=False,
                count=count,
            )

            device_info = {
                'barcode': barcode,
                'brand_name': brand_name,
                'company_name': company_name,
                'device_description': device_description,
                'item_description': item_details["item_description"],
                'expiration_date': expiration_date,
                'version_model_number': version_model_number,
                'catalog_number': catalog_number,
                'item_name': item_details["item_name"],
                'labeled_contains_nrl': labeled_contains_nrl
            }

            return render(request, 'result.html', {'device_data': device_info})

        return render(request, 'scanner.html')

def export_to_excel(request):
    """
    Export scan history to an Excel file with the server's local time.
    """
    scans = ScanRecord.objects.all().values()
    if not scans:
        return HttpResponse("No data to export", content_type="text/plain")

    df = pd.DataFrame(scans)
    if "scan_time" in df.columns:
        df["scan_time"] = df["scan_time"].apply(
            lambda x: localtime(x).replace(tzinfo=None) if pd.notnull(x) else x
        )

    df.rename(columns={
        "scan_time": "Scan Time (Server Time)",
        "barcode": "Barcode",
        "brand_name": "Brand Name",
        "company_name": "Company Name",
        "device_description": "Device Description",
        "item_description": "Item Description",
        "expiration_date": "Expiration Date",
        "version_model_number": "Version/Model Number",
        "item_name": "Item Name",
        "labeled_contains_nrl": "Labeled Contains NRL"
    }, inplace=True)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="scan_history.xlsx"'
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

    return response

def export_scan_history_to_server():
    """
    Export scan history to an Excel file with a timestamp for backup purposes.
    """
    scans = ScanRecord.objects.all().values()
    if not scans:
        return None

    df = pd.DataFrame(scans)
    if "scan_time" in df.columns:
        df["scan_time"] = df["scan_time"].apply(
            lambda x: localtime(x).replace(tzinfo=None) if pd.notnull(x) else x
        )

    df.rename(columns={
        "scan_time": "Scan Time (Server Time)",
        "barcode": "Barcode",
        "brand_name": "Brand Name",
        "company_name": "Company Name",
        "device_description": "Device Description",
        "item_description": "Item Description",
        "expiration_date": "Expiration Date",
        "version_model_number": "Version/Model Number",
        "item_name": "Item Name",
        "labeled_contains_nrl": "Labeled Contains NRL"
    }, inplace=True)

    backup_dir = os.path.join(settings.MEDIA_ROOT, "scan_backups")
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_filename = os.path.join(backup_dir, f"scan_history_backup_{timestamp}.xlsx")

    with pd.ExcelWriter(backup_filename, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

    return backup_filename

def clear_scan_history(request):
    """
    Save scan history before deleting all scan records from the database.
    """
    backup_file = export_scan_history_to_server()
    ScanRecord.objects.all().delete()
    if backup_file:
        print(f"✅ Backup saved at: {backup_file}")
    return redirect('scan_history')

def scan_history(request):
    """
    Show all past scans with search functionality and options to export or clear data.
    """
    query = request.GET.get('q', '')
    if query:
        scans = ScanRecord.objects.filter(
            Q(barcode__icontains=query) |
            Q(brand_name__icontains=query) |
            Q(company_name__icontains=query) |
            Q(device_description__icontains=query) |
            Q(item_description__icontains=query) |
            Q(expiration_date__icontains=query) |
            Q(version_model_number__icontains=query) |
            Q(item_name__icontains=query) |
            Q(labeled_contains_nrl__icontains=query)
        ).order_by('-scan_time')
    else:
        scans = ScanRecord.objects.order_by('-scan_time')
    return render(request, 'scan_history.html', {'scans': scans, 'query': query})

def edit_scan(request, scan_id):
    """
    Edit an existing scan record.
    """
    scan = get_object_or_404(ScanRecord, id=scan_id)
    if request.method == 'POST':
        form = EditScanForm(request.POST, request.FILES, instance=scan)
        if form.is_valid():
            form.save()
            return redirect('scan_history')
    else:
        form = EditScanForm(instance=scan)
    return render(request, 'edit_scan.html', {'form': form, 'scan': scan})

def capture_image(request):
    """
    Handles image capture and stores the missing barcode in the database while preserving known values.
    """
    if request.method == 'POST' and request.FILES.get('image'):
        barcode = sanitize_filename(request.POST.get('barcode'))
        image = request.FILES['image']
        image_name = f"{barcode}{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        image_path = os.path.join("missing_scans", image_name)
        saved_path = default_storage.save(image_path, ContentFile(image.read()))
        existing_scan = ScanRecord.objects.filter(barcode=barcode).first()

        if existing_scan:
            existing_scan.image = saved_path
            existing_scan.save()
        else:
            ScanRecord.objects.create(
                barcode=barcode,
                brand_name=request.POST.get("brand_name", "Unknown"),
                company_name=request.POST.get("company_name", "Unknown"),
                device_description=request.POST.get("device_description", "-"),
                item_description=request.POST.get("item_description", "Unknown"),
                expiration_date=request.POST.get("expiration_date", "Unknown"),
                version_model_number=request.POST.get("version_model_number", "Unknown"),
                item_name=request.POST.get("item_name", "Item Not Found"),
                labeled_contains_nrl=request.POST.get("labeled_contains_nrl", "Unknown"),
                scan_time=datetime.datetime.now(),
                is_manual_entry=True,
                image=saved_path
            )
        return redirect('scan_page')
    return redirect('scan_page')

def uploading_page(request):
    """Displays the uploading screen while the image is being processed."""
    return render(request, 'uploading.html')

def add_placeholder_scan(request, action):
    """
    Adds a 'Next Shelf', 'Next Rack', or 'Next Hanger' placeholder entry in the database.
    """
    if action == "shelf":
        placeholder_text = "Next Shelf"
    elif action == "rack":
        placeholder_text = "Next Rack"
    elif action == "hanger":
        placeholder_text = "Next Hanger"
    else:
        return redirect('scan_page')

    ScanRecord.objects.create(
        barcode=placeholder_text,
        brand_name=placeholder_text,
        company_name=placeholder_text,
        device_description=placeholder_text,
        expiration_date="n/a",
        version_model_number=placeholder_text,
        count=0,
        scan_time=datetime.datetime.now()
    )
    return redirect('scan_page')

def delete_scan(request, scan_id):
    """Delete a scan record and optionally its associated image."""
    scan = get_object_or_404(ScanRecord, id=scan_id)
    # Optionally delete the image file if needed:
    # if scan.image:
    #     scan.image.delete()
    scan.delete()
    messages.success(request, "Scan deleted successfully.")
    return redirect('scan_history')

def search_ref(request):
    """
    Search for an item in SQLite using TP Item Number (REF Number) and return details.
    """
    ref_number = request.GET.get("ref", "").strip()
    barcode = request.GET.get("barcode", "").strip()

    if not ref_number:
        return JsonResponse({"success": False, "message": "No REF number provided."})

    try:
        item_details = find_item_details(ref_number)
        if barcode.startswith("unknown_"):
            barcode = barcode.replace("unknown_", "", 1)
        logging.info(f"Item details fetched: {item_details}")
        return JsonResponse({
            "success": True,
            "barcode": barcode,
            "brand_name": item_details["trading_partner_name"],
            "company_name": item_details["trading_partner_name"],
            "device_description": "Needs manual entry",
            "item_description": item_details["item_description"],
            "expiration_date": "Unknown",
            "version_model_number": ref_number,
            "item_name": item_details["item_name"],
            "labeled_contains_nrl": "Unknown",
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})

def upload_items(request):
    """
    Handles file upload and appends only new items to the database.
    """
    if request.method == "POST" and request.FILES.get("file"):
        file = request.FILES["file"]
        file_extension = file.name.split(".")[-1]
        file_path = default_storage.save(f"uploads/{file.name}", ContentFile(file.read()))

        try:
            if file_extension == "csv":
                df = pd.read_csv(file_path)
            elif file_extension in ["xls", "xlsx"]:
                df = pd.read_excel(file_path)
            else:
                messages.error(request, "Unsupported file format. Please upload a CSV or Excel file.")
                return redirect("upload_page")

            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                new_items = 0
                for _, row in df.iterrows():
                    tp_item_number = row.get("TP Item Number")
                    if not tp_item_number:
                        continue

                    cursor.execute("SELECT COUNT(*) FROM items WHERE `TP Item Number` = ?", (tp_item_number,))
                    exists = cursor.fetchone()[0] > 0

                    if not exists:
                        cursor.execute(
                            """INSERT INTO items 
                            ("Item Name", "Item Status", "Template Name", "Item Class Name", "Item Description",
                             "Item Long Description", "Trading Partner Type", "Trading Partner Name",
                             "TP Item Number", "UNSPSC", "Category Name", "Item Primary Unit of Measure",
                             "Packaging String", "Organization Name", "Epic Item", "Implant",
                             "Epic Item Category", "Patient Chargeable", "Epic CDM", "WellSpan Tracked",
                             "Reprocessed", "UNSPSC.1", "Latex Indicator", "HCPCS Code", "Lawson Number")
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            tuple(row)
                        )
                        new_items += 1
                conn.commit()

            messages.success(request, f"{new_items} new items added successfully.")
            return redirect("upload_page")

        except Exception as e:
            messages.error(request, f"Error processing file: {str(e)}")
            return redirect("upload_page")

    return render(request, "upload.html")

@csrf_exempt
def update_ngrok_url(request):
    """
    Update the global ngrok URL used for sending print jobs.
    """
    global current_ngrok_url
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            new_url = data.get("ngrok_url")
            if new_url:
                current_ngrok_url = new_url
                return JsonResponse({"message": "ngrok URL updated successfully!", "ngrok_url": new_url}, status=200)
            else:
                return JsonResponse({"error": "Invalid URL"}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def send_to_printer(request):
    """
    Sends print data to the configured printer via the ngrok URL.
    """
    global current_ngrok_url
    if request.method == "POST":
        if not current_ngrok_url:
            return JsonResponse({"error": "Printer service unavailable. Please update the ngrok URL."}, status=500)
        try:
            data = json.loads(request.body)
            text_to_print = (
                f"Brand: {data.get('company_name', 'Unknown')}\n"
                f"Item#: {data.get('item_name', 'Unknown')}\n"
                f"Description: {data.get('item_description', 'No Description')}\n"
                f"Barcode: {data.get('barcode', '')}\n"
                f"MFR#: {data.get('version_model_number', 'Unknown')}\n"
            )
            response = requests.post(current_ngrok_url, data=text_to_print, headers={"Content-Type": "text/plain"})
            if response.status_code == 200:
                return JsonResponse({"message": "Print job sent successfully!"}, status=200)
            else:
                logging.error(f"Printing failed: {response.text}")
                return JsonResponse({"error": f"Failed to print: {response.text}"}, status=500)
        except json.JSONDecodeError:
            logging.error("Invalid JSON received in print request")
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
    return JsonResponse({"error": "Invalid request method"}, status=405)

def scan_page(request):
    """
    Render the scanner page and display the last scanned item.
    """
    last_scanned = ScanRecord.objects.order_by('-scan_time').first()
    return render(request, 'scanner.html', {"last_scanned_item": last_scanned})

def backup_list(request):
    """
    Fetch and display a list of all backup files.
    """
    backup_dir = os.path.join(settings.MEDIA_ROOT, "scan_backups")
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    backup_files = sorted(
        [f for f in os.listdir(backup_dir) if f.endswith(".xlsx")],
        reverse=True
    )
    return render(request, "backup_list.html", {"backup_files": backup_files, "media_url": settings.MEDIA_URL})

def restore_backup(request):
    """
    Append scan history from a selected backup without deleting existing records.
    """
    if request.method == "POST":
        backup_filename = request.POST.get("backup_filename")
        backup_dir = os.path.join(settings.MEDIA_ROOT, "scan_backups")
        backup_path = os.path.join(backup_dir, backup_filename)
        if os.path.exists(backup_path):
            try:
                df = pd.read_excel(backup_path, dtype=str)
                count_added = 0
                for _, row in df.iterrows():
                    scan_time_str = row.get("Scan Time (Server Time)")
                    if scan_time_str:
                        try:
                            scan_time = datetime.datetime.strptime(scan_time_str, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            scan_time = None
                    else:
                        scan_time = None

                    ScanRecord.objects.create(
                        id=row.get("id"),
                        barcode=row.get("Barcode"),
                        brand_name=row.get("Brand Name") or None,
                        company_name=row.get("Company Name") or None,
                        device_description=row.get("Device Description") or None,
                        item_description=row.get("Item Description") or None,
                        expiration_date=row.get("Expiration Date") or None,
                        version_model_number=row.get("Version/Model Number") or None,
                        item_name=row.get("Item Name") or None,
                        labeled_contains_nrl=row.get("Labeled Contains NRL") or None,
                        scan_time=scan_time,
                    )
                    count_added += 1

                if count_added > 0:
                    messages.success(request, f"✅ {count_added} new records appended from '{backup_filename}'!")
                else:
                    messages.warning(request, f"⚠️ No new records were added. All entries already exist.")
            except Exception as e:
                messages.error(request, f"❌ Error restoring backup: {e}")
        else:
            messages.error(request, f"❌ Backup file not found: {backup_path}")
    return redirect("backup_list")
