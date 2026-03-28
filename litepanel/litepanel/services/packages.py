"""Package management service."""
import subprocess

def is_installed(pkg_name):
    """Check if a package is installed using dpkg."""
    try:
        subprocess.check_output(['dpkg', '-s', pkg_name], stderr=subprocess.STDOUT)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def get_packages_status():
    """Return a dictionary of supported packages and their statuses."""
    packages = {
        'mariadb-server': {
            'id': 'mariadb-server',
            'name': 'MariaDB Server',
            'installed': is_installed('mariadb-server'),
            'description': 'Core database server (required for websites and FTP).',
            'icon': 'ph-database'
        },
        'pure-ftpd': {
            'id': 'pure-ftpd',
            'name': 'Pure-FTPd',
            'installed': is_installed('pure-ftpd'),
            'description': 'Lightweight FTP server for website file management.',
            'icon': 'ph-cloud-arrow-up'
        },
        'fail2ban': {
            'id': 'fail2ban',
            'name': 'Fail2Ban',
            'installed': is_installed('fail2ban'),
            'description': 'Brute-force protection for your server ports.',
            'icon': 'ph-shield-check'
        }
    }
    return packages

def install_pkg(pkg_name):
    """Install a package via apt-get."""
    try:
        # Update first (simple sync call)
        subprocess.run(['sudo', 'apt-get', 'update', '-y'], check=True, capture_output=True)
        subprocess.run(['sudo', 'apt-get', 'install', '-y', pkg_name], check=True, capture_output=True)
        
        # Post-install config for specific packages
        if pkg_name == 'mariadb-server':
            subprocess.run(['sudo', 'systemctl', 'enable', '--now', 'mariadb'], check=False)
        elif pkg_name == 'pure-ftpd':
            subprocess.run(['sudo', 'systemctl', 'enable', '--now', 'pure-ftpd'], check=False)
            
        return True, "Installation successful."
    except subprocess.CalledProcessError as e:
        return False, f"Installation failed: {e.stderr.decode() if e.stderr else str(e)}"
