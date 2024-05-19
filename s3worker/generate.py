from pathlib import Path
from uuid import UUID
from sqlalchemy.orm import Session

from s3worker import db, image
from s3worker import constants as const
from s3worker import pathlib as plib


def doc_thumbnail(
    db_session: Session,
    doc_id: UUID,
    size: int = const.DEFAULT_THUMBNAIL_SIZE
) -> Path:
    last_ver = db.get_last_version(db_session, doc_id)
    # first page of the doc's last version
    first_page_uid = db.get_first_page_uuid(db_session, last_ver.id)
    abs_thumbnail_path = plib.rel2abs(
        plib.thumbnail_path(first_page_uid, size=size)
    )
    pdf_path = last_ver.abs_file_path
    image.generate_preview(
        pdf_path=pdf_path,
        output_folder=abs_thumbnail_path.parent,
        size=size
    )

    return plib.thumbnail_path(first_page_uid, size=size)


def doc_previews(doc_id: UUID):
    pass
