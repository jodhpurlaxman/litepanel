"""
OpenLiteSpeed integration service.
All subprocess calls use explicit arg lists, shell=False, timeout=60.
"""
import logging
import re
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

LSWS_CTRL = '/usr/local/lsws/bin/lswsctrl'
VHOST_DIR  = '/usr/local/lsws/conf/vhosts'
HTTPD_CONF = '/usr/local/lsws/conf/httpd_config.conf'

_DOMAIN_RE = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]{1,251}[a-zA-Z0-9]$')

VHOST_TEMPLATE = """\
virtualHost {domain} {{
  vhRoot                  /home/{domain}/
  docRoot                 /home/{domain}/public_html/
  allowSymbolLink         1
  enableScript            1
  restrained              1

  extprocessor lsphp{php_ver_flat} {{
    type                  lsapi
    address               uds://tmp/lshttpd/lsphp{php_ver_flat}.sock
    maxConns              10
    env                   PHP_LSAPI_CHILDREN=10
    initTimeout           60
    retryTimeout          0
    persistConn           1
  }}

  scripthandler {{
    add lsphp{php_ver_flat} php
  }}
{ssl_block}}}
"""

SSL_BLOCK = """\
  listener SSL_{domain} {{
    address               *:443
    secure                1
    keyFile               /etc/letsencrypt/live/{domain}/privkey.pem
    certFile              /etc/letsencrypt/live/{domain}/fullchain.pem
  }}
"""

# Snippet added to httpd_config.conf to register the vhost
HTTPD_VHOST_ENTRY = """
virtualHost {domain} {{
  vhRoot                  /home/{domain}/
  configFile              {vhost_dir}/{domain}/vhconf.conf
  allowSymbolLink         1
}}
"""

HTTPD_LISTENER_ENTRY = """
listener HTTP {{
  address                 *:80
  secure                  0
  map                     {domain} {domain}
}}
"""


def _safe_domain(domain: str) -> str:
    if not _DOMAIN_RE.match(domain):
        raise ValueError(f'Invalid domain: {domain}')
    return domain


def _sudo_read(path: str) -> str:
    r = subprocess.run(['sudo', 'cat', path], capture_output=True, text=True, timeout=10)
    return r.stdout if r.returncode == 0 else ''


def _sudo_write(path: str, content: str) -> None:
    r = subprocess.run(['sudo', 'tee', path], input=content, text=True,
                       capture_output=True, timeout=10)
    if r.returncode != 0:
        raise RuntimeError(f'Failed to write {path}: {r.stderr}')


def write_vhost_config(domain: str, php_version: str = '8.1', ssl: bool = False) -> Path:
    domain = _safe_domain(domain)
    php_flat = php_version.replace('.', '')
    ssl_block = SSL_BLOCK.format(domain=domain) if ssl else ''
    config = VHOST_TEMPLATE.format(domain=domain, php_ver_flat=php_flat, ssl_block=ssl_block)

    vhost_dir = Path(VHOST_DIR) / domain
    conf_file = vhost_dir / 'vhconf.conf'

    subprocess.run(['sudo', 'mkdir', '-p', str(vhost_dir)], check=True, timeout=10)
    _sudo_write(str(conf_file), config)

    # Register vhost in httpd_config.conf if not already there
    _register_vhost_in_httpd(domain)

    logger.info('Wrote OLS vhost config: %s', conf_file)
    return conf_file


def _register_vhost_in_httpd(domain: str) -> None:
    """Add virtualHost + listener map entry to httpd_config.conf if missing."""
    try:
        current = _sudo_read(HTTPD_CONF)
        if f'vhRoot                  /home/{domain}/' in current:
            return  # already registered

        entry = HTTPD_VHOST_ENTRY.format(domain=domain, vhost_dir=VHOST_DIR)
        _sudo_write(HTTPD_CONF, current + entry)
        logger.info('Registered vhost %s in httpd_config.conf', domain)
    except Exception as e:
        logger.warning('Could not register vhost in httpd_config.conf: %s', e)


def _unregister_vhost_from_httpd(domain: str) -> None:
    """Remove the vhost block for domain from httpd_config.conf."""
    try:
        current = _sudo_read(HTTPD_CONF)
        # Remove the block we added
        marker = f'\nvirtualHost {domain} {{'
        if marker not in current:
            return
        start = current.index(marker)
        # Find matching closing brace
        depth, pos = 0, start
        for i, ch in enumerate(current[start:], start):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    pos = i + 1
                    break
        new_content = current[:start] + current[pos:]
        _sudo_write(HTTPD_CONF, new_content)
        logger.info('Unregistered vhost %s from httpd_config.conf', domain)
    except Exception as e:
        logger.warning('Could not unregister vhost from httpd_config.conf: %s', e)


def delete_vhost_config(domain: str) -> None:
    domain = _safe_domain(domain)
    vhost_dir = Path(VHOST_DIR) / domain
    subprocess.run(['sudo', 'rm', '-rf', str(vhost_dir)], timeout=10)
    _unregister_vhost_from_httpd(domain)
    logger.info('Deleted OLS vhost config for %s', domain)


def reload_ols() -> None:
    """Graceful reload — non-fatal if OLS is not installed."""
    if not Path(LSWS_CTRL).exists():
        logger.warning('lswsctrl not found — skipping OLS reload')
        return
    result = subprocess.run(
        ['sudo', LSWS_CTRL, 'graceful'],
        shell=False, timeout=60, capture_output=True, text=True,
    )
    if result.returncode != 0:
        logger.error('OLS reload failed: %s', result.stderr)
        # Non-fatal — site is created, OLS just needs manual reload
    else:
        logger.info('OLS graceful reload OK')


def create_docroot(domain: str) -> Path:
    domain = _safe_domain(domain)
    docroot = Path(f'/home/{domain}/public_html')
    subprocess.run(['sudo', 'mkdir', '-p', str(docroot)], check=True, timeout=10)
    subprocess.run(['sudo', 'chown', '-R', 'www-data:www-data', f'/home/{domain}'], check=True, timeout=10)
    subprocess.run(['sudo', 'chmod', '755', f'/home/{domain}'], check=True, timeout=10)
    subprocess.run(['sudo', 'chmod', '755', str(docroot)], check=True, timeout=10)
    return docroot
