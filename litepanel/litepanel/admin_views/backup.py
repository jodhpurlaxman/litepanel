"""Configuration export — admin only."""
import json
from datetime import datetime, timezone
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods

from litepanel.models import Website, User
from litepanel.admin_views.decorators import admin_required

PANEL_VERSION = '1.0.0'


@admin_required
@require_http_methods(['GET'])
def export_websites(request):
    sites = []
    for s in Website.objects.select_related('owner').all():
        sites.append({
            'id': s.pk, 'domain': s.domain, 'doc_root': s.doc_root,
            'php_version': s.php_version, 'ssl_enabled': s.ssl_enabled,
            'owner': s.owner.username, 'created_at': s.created_at.isoformat(),
        })
    payload = json.dumps({
        'export_timestamp': datetime.now(timezone.utc).isoformat(),
        'panel_version': PANEL_VERSION,
        'websites': sites,
    }, indent=2)
    return HttpResponse(payload, content_type='application/json',
                        headers={'Content-Disposition': 'attachment; filename="websites_export.json"'})


@admin_required
@require_http_methods(['GET'])
def export_users(request):
    users = []
    for u in User.objects.all():
        users.append({
            'id': u.pk, 'username': u.username, 'email': u.email,
            'role': u.role, 'is_active': u.is_active, 'created_at': u.created_at.isoformat(),
            # password hash and API tokens intentionally excluded
        })
    payload = json.dumps({
        'export_timestamp': datetime.now(timezone.utc).isoformat(),
        'panel_version': PANEL_VERSION,
        'users': users,
    }, indent=2)
    return HttpResponse(payload, content_type='application/json',
                        headers={'Content-Disposition': 'attachment; filename="users_export.json"'})
