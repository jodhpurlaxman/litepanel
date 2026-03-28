"""Package management — admin views."""
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect

from litepanel.admin_views.decorators import admin_required
from litepanel.services.packages import get_packages_status, install_pkg

@admin_required
@require_http_methods(['GET'])
def list_packages(request):
    """Render the packages management page."""
    packages = get_packages_status()
    return render(request, 'admin/packages.html', {
        'packages': packages,
        'active_page': 'packages',
        'panel_user': request.panel_user
    })

@admin_required
@csrf_protect
@require_http_methods(['POST'])
def trigger_install(request):
    """Trigger installation of a specific package."""
    try:
        data = json.loads(request.body)
        pkg_id = data.get('package_id')
        if not pkg_id:
            return JsonResponse({'error': 'Missing package ID'}, status=400)
            
        success, message = install_pkg(pkg_id)
        if success:
            return JsonResponse({'status': 'success', 'message': message})
        else:
            return JsonResponse({'status': 'error', 'message': message}, status=500)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
