"""Website management — user views."""
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from litepanel.models import Website

@require_http_methods(['GET'])
def user_dashboard(request):
    # Only show websites owned by the logged-in user
    user_id = request.session.get('user_id')
    sites = Website.objects.filter(owner_id=user_id).order_by('-created_at')
    return render(request, 'user/dashboard.html', {
        'websites': sites,
        'active_page': 'websites'
    })
