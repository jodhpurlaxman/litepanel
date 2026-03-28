"""Backup management — admin views."""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from litepanel.admin_views.decorators import admin_required

@admin_required
@require_http_methods(['GET'])
def list_backups(request):
    """Render the backup management dashboard."""
    # Placeholder for now
    backups = [] 
    return render(request, 'admin/backup.html', {
        'backups': backups,
        'active_page': 'backup',
        'panel_user': request.panel_user
    })

@admin_required
def export_websites(request):
    return JsonResponse({'status': 'stub'})

@admin_required
def export_users(request):
    return JsonResponse({'status': 'stub'})
