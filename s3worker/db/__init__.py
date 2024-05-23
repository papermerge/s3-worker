from uuid import UUID

from .doc_ver import get_last_version, get_pages
from .session import get_db

__all__ = [
    'get_last_version',
    'get_pages',
    'get_db'
]
