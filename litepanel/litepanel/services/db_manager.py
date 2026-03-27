"""
MariaDB/MySQL database management service.
Creates isolated databases and users for hosted websites.
"""
import logging
import re

import django.db

logger = logging.getLogger(__name__)

_NAME_RE = re.compile(r'^[a-zA-Z0-9_]{1,64}$')


def _safe_name(name: str) -> str:
    if not _NAME_RE.match(name):
        raise ValueError(f'Invalid database/user name: {name}')
    return name


def _get_cursor():
    from django.db import connections
    return connections['default'].cursor()


def create_database(website, db_name: str) -> 'Database':
    from litepanel.models import Database
    db_name = _safe_name(db_name)
    db_user = _safe_name(db_name + '_u')[:64]

    import secrets
    db_pass = secrets.token_urlsafe(24)

    with _get_cursor() as cursor:
        cursor.execute(f'CREATE DATABASE `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
        cursor.execute(f"CREATE USER '{db_user}'@'localhost' IDENTIFIED BY %s", [db_pass])
        cursor.execute(f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{db_user}'@'localhost'")
        cursor.execute('FLUSH PRIVILEGES')

    db = Database.objects.create(website=website, db_name=db_name, db_user=db_user)
    logger.info('Created database %s for %s', db_name, website.domain)
    return db


def delete_database(database) -> None:
    db_name = _safe_name(database.db_name)
    db_user = _safe_name(database.db_user)

    with _get_cursor() as cursor:
        cursor.execute(f'DROP DATABASE IF EXISTS `{db_name}`')
        cursor.execute(f"DROP USER IF EXISTS '{db_user}'@'localhost'")
        cursor.execute('FLUSH PRIVILEGES')

    database.delete()
    logger.info('Deleted database %s', db_name)
