from uuid import UUID
from s3worker import db
from s3worker import constants as const
from s3worker import pathlib as plib


def doc_thumbnail(
    doc_id: UUID,
    size: int = const.DEFAULT_THUMBNAIL_SIZE
):
    last_ver = db.get_last_version(doc_id)
    # first page of the doc's last version
    first_page_uid = db.get_first_page_uuid(last_ver.id)
    abs_thumbnail_path = plib.rel2abs(
        plib.thumbnail_path(first_page_uid, size=size)
    )
    pdf_path = last_ver.file_path

def doc_ver_previews(doc_id: UUID):
    pass
