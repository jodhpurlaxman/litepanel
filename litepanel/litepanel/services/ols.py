"""
OpenLiteSpeed integration service.
All subprocess calls use explicit arg lists, shell=False, timeout=60.
"""
import logging
import os
import re
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

LSWS_CTRL = '/usr/local/lsws/bin/lswsctrl'
VHOST_DIR = '/usr/local/lsws/conf/vhosts'

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


def _safe_domain(domain: str) -> str:
    if not _DOMAIN_RE.match(domain):
        raise ValueError(f'Invalid domain: {domain}')
    return domain


def write_vhost_config(domain: str, php_version: str = '8.1', ssl: bool = False) -> Path:
    domain = _safe_domain(domain)
    php_flat = php_version.replace('.', '')
    ssl_block = SSL_BLOCK.format(domain=domain) if ssl else ''
    config = VHOST_TEMPLATE.format(domain=domain, php_ver_flat=php_flat, ssl_block=ssl_block)

    vhost_path = Path(VHOST_DIR) / domain
    vhost_path.mkdir(parents=True, exist_ok=True)
    conf_file = vhost_path / 'vhconf.conf'
    conf_file.write_text(config)
    logger.info('Wrote OLS vhost config: %s', conf_file)
    return conf_file


def delete_vhost_config(domain: str) -> None:
    domain = _safe_domain(domain)
    conf_file = Path(VHOST_DIR) / domain / 'vhconf.conf'
    if conf_file.exists():
        conf_file.unlink()
        logger.info('Deleted OLS vhost config: %s', conf_file)


def reload_ols() -> None:
    result = subprocess.run(
        ['sudo', LSWS_CTRL, 'graceful'],
        shell=False,
        timeout=60,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error('OLS reload failed: %s', result.stderr)
        raise RuntimeError(f'OLS reload failed: {result.stderr[:512]}')
    logger.info('OLS graceful reload OK')


def create_docroot(domain: str) -> Path:
    domain = _safe_domain(domain)
    docroot = Path(f'/home/{domain}/public_html')
    
    # Use sudo to create directories in /home as the litepanel user cannot
    subprocess.run(['sudo', 'mkdir', '-p', str(docroot)], check=True)
    subprocess.run(['sudo', 'chown', '-R', 'www-data:www-data', f'/home/{domain}'], check=True)
    subprocess.run(['sudo', 'chmod', '755', f'/home/{domain}'], check=True)
    subprocess.run(['sudo', 'chmod', '755', str(docroot)], check=True)
    
    return docroot
