from django.urls import path
from .views import backup_list, lookup_gudid, restore_backup, scan_page, scan_history, export_to_excel, clear_scan_history, capture_image, edit_scan, add_placeholder_scan, delete_scan, search_ref, send_to_printer, update_ngrok_url, upload_items
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', scan_page, name='scan_page'),
    path('lookup/', lookup_gudid, name='lookup_gudid'),
    path('history/', scan_history, name='scan_history'),
    path('export/', export_to_excel, name='export_to_excel'),
    path('clear/', clear_scan_history, name='clear_scan_history'),
    path('capture/', capture_image, name='capture_image'),
    path('edit/<int:scan_id>/', edit_scan, name='edit_scan'),
    path('next/<str:action>/', add_placeholder_scan, name='add_placeholder_scan'),
    path('delete-scan/<int:scan_id>/', delete_scan, name='delete_scan'),
    path('search-ref/', search_ref, name='search_ref'),
    path("upload/", upload_items, name="upload_page"),
    path("update-ngrok-url", update_ngrok_url, name="update-ngrok-url"),
    path("send-to-printer/", send_to_printer, name="send_to_printer"),
    path('backups/', backup_list, name='backup_list'),
    path('backups/restore/', restore_backup, name='restore_backup')


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

