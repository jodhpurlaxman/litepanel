"""URL configuration for Lite Hosting Panel."""
from django.urls import path
from litepanel.views.auth import login_index, admin_login, user_login, logout_view
from litepanel.admin_views import users as au, websites as aw, backup as ab, packages as ap
from litepanel.user_views import ftp as uf, git as ug, ssl as us, databases as ud, websites as uw
from litepanel.api import views as av

urlpatterns = [
    # ── Login / logout ────────────────────────────────────────────────────
    path('',          login_index,  name='login_index'),   # Auto-detect port
    path('login/',    user_login,   name='user_login'),    # port 2083 root
    path('logout/',   logout_view,  name='logout'),

    # ── Admin views ───────────────────────────────────────────────────────
    path('admin/dashboard/',                aw.admin_dashboard,  name='admin_dashboard'),
    path('admin/users/',                    au.list_users,      name='admin_list_users'),
    path('admin/packages/',                 ap.list_packages,    name='admin_list_packages'),
    path('admin/packages/install/',         ap.trigger_install,   name='admin_install_package'),
    path('admin/users/create/',             au.create_user,     name='admin_create_user'),
    path('admin/users/<int:user_id>/delete/', au.delete_user,   name='admin_delete_user'),
    path('admin/users/<int:user_id>/reset-password/', au.reset_password, name='admin_reset_password'),

    path('admin/websites/',                       aw.list_websites,    name='admin_list_websites'),
    path('admin/websites/create/',                aw.create_website,   name='admin_create_website'),
    path('admin/websites/<int:site_id>/delete/',  aw.delete_website,   name='admin_delete_website'),
    path('admin/websites/<int:site_id>/config/',  aw.configure_website,name='admin_config_website'),

    path('admin/export/websites/', ab.export_websites, name='admin_export_websites'),
    path('admin/export/users/',    ab.export_users,    name='admin_export_users'),

    # ── User views ────────────────────────────────────────────────────────
    path('user/dashboard/',                 uw.user_dashboard,  name='user_dashboard'),
    path('user/sites/<int:site_id>/ftp/',                        uf.list_ftp,     name='user_list_ftp'),
    path('user/sites/<int:site_id>/ftp/create/',                 uf.create_ftp,   name='user_create_ftp'),
    path('user/sites/<int:site_id>/ftp/<int:account_id>/delete/',uf.delete_ftp,   name='user_delete_ftp'),
    path('user/sites/<int:site_id>/ftp/<int:account_id>/passwd/',uf.change_ftp_pw,name='user_ftp_passwd'),

    path('user/sites/<int:site_id>/git/',         ug.list_repos, name='user_list_git'),
    path('user/sites/<int:site_id>/git/link/',    ug.link_repo,  name='user_link_git'),
    path('user/sites/<int:site_id>/git/pull/',    ug.git_pull,   name='user_git_pull'),
    path('user/sites/<int:site_id>/git/push/',    ug.git_push,   name='user_git_push'),

    path('user/sites/<int:site_id>/ssl/',         us.ssl_status, name='user_ssl_status'),
    path('user/sites/<int:site_id>/ssl/request/', us.request_ssl,name='user_ssl_request'),

    path('user/sites/<int:site_id>/databases/',                    ud.list_databases, name='user_list_db'),
    path('user/sites/<int:site_id>/databases/create/',             ud.create_db,      name='user_create_db'),
    path('user/sites/<int:site_id>/databases/<int:db_id>/delete/', ud.delete_db,      name='user_delete_db'),

    # ── REST API ──────────────────────────────────────────────────────────
    path('api/v1/websites/',              av.websites,       name='api_websites'),
    path('api/v1/websites/<int:site_id>/',av.website_detail, name='api_website_detail'),
    path('api/v1/users/',                 av.users,          name='api_users'),
    path('api/v1/ftp/',                   av.ftp_accounts,   name='api_ftp'),
    path('api/v1/ssl/',                   av.ssl_certs,      name='api_ssl'),
    path('api/v1/git/',                   av.git_repos,      name='api_git'),
    path('api/v1/databases/',             av.databases,      name='api_databases'),
    path('api/v1/tokens/create/',         av.create_token,   name='api_create_token'),
]
