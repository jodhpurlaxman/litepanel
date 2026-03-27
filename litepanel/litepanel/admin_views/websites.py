"""Website management — admin views."""
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect

from litepanel.models import Website, User
from litepanel.admin_views.decorators import admin_required
from litepanel.audit import log_action
from litepanel.services import ols


@admin_required
@require_http_methods(['GET'])
def list_websites(request):
    sites = list(Website.objects.values('id', 'domain', 'doc_root', 'php_version', 'ssl_enabled', 'created_at'))
    return JsonResponse({'websites': sites})


@admin_required
@csrf_protect
@require_http_methods(['POST'])
def create_website(request):
    data = json.loads(request.body)
    domain = data.get('domain', '').strip().lower()
    owner_id = data.get('owner_id')
    php_version = data.get('php_version', '8.1')

    try:
        owner = User.objects.get(pk=owner_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Owner not found', 'code': 'NOT_FOUND', 'details': {}}, status=400)

    if Website.objects.filter(domain=domain).exists():
        return JsonResponse({'error': 'Domain already exists', 'code': 'DUPLICATE_DOMAIN', 'details': {}}, status=400)

    try:
        site = Website(owner=owner, domain=domain, php_version=php_version)
        site.full_clean()
        site.save()
        ols.create_docroot(domain)
        ols.write_vhost_config(domain, php_version)
        ols.reload_ols()
    except Exception as e:
        return JsonResponse({'error': str(e), 'code': 'CREATE_FAILED', 'details': {}}, status=400)

    log_action(request.panel_user, 'website_create', domain, request.META.get('REMOTE_ADDR', '0.0.0.0'))
    return JsonResponse({'id': site.pk, 'domain': site.domain, 'doc_root': site.doc_root}, status=201)


@admin_required
@csrf_protect
@require_http_methods(['POST'])
def delete_website(request, site_id):
    data = json.loads(request.body)
    if not data.get('confirm'):
        return JsonResponse({'error': 'Confirmation required', 'code': 'CONFIRM_REQUIRED', 'details': {}}, status=400)

    try:
        site = Website.objects.get(pk=site_id)
    except Website.DoesNotExist:
        return JsonResponse({'error': 'Website not found', 'code': 'NOT_FOUND', 'details': {}}, status=404)

    domain = site.domain
    delete_files = data.get('delete_files', False)

    # Remove OLS config
    ols.delete_vhost_config(domain)

    # Optionally remove files
    if delete_files:
        import shutil
        import pathlib
        home = pathlib.Path(f'/home/{domain}')
        if home.exists():
            shutil.rmtree(str(home))

    # Cascade handled by Django FK (FTPAccounts, SSLCertificate, etc.)
    site.delete()
    ols.reload_ols()

    log_action(request.panel_user, 'website_delete', domain, request.META.get('REMOTE_ADDR', '0.0.0.0'))
    return JsonResponse({'deleted': domain})


@admin_required
@csrf_protect
@require_http_methods(['POST'])
def configure_website(request, site_id):
    data = json.loads(request.body)
    try:
        site = Website.objects.get(pk=site_id)
    except Website.DoesNotExist:
        return JsonResponse({'error': 'Website not found', 'code': 'NOT_FOUND', 'details': {}}, status=404)

    php_version = data.get('php_version', site.php_version)
    site.php_version = php_version
    site.save(update_fields=['php_version'])

    try:
        ols.write_vhost_config(site.domain, php_version, ssl=site.ssl_enabled)
        ols.reload_ols()
    except Exception as e:
        return JsonResponse({'error': str(e), 'code': 'CONFIG_FAILED', 'details': {}}, status=500)

    log_action(request.panel_user, 'website_config', site.domain, request.META.get('REMOTE_ADDR', '0.0.0.0'))
    return JsonResponse({'domain': site.domain, 'php_version': php_version})
