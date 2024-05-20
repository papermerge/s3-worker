import logging
from pathlib import Path
from uuid import UUID
from sqlalchemy.orm import Session

from s3worker import db, image
from s3worker import constants as const
from s3worker import pathlib as plib


logger = logging.getLogger(__name__)


def doc_thumbnail(
    db_session: Session,
    doc_id: UUID,
    size: int = const.DEFAULT_THUMBNAIL_SIZE
) -> Path:
    logger.info(f"Generating thumbnail for {doc_id}")

    last_ver = db.get_last_version(db_session, doc_id)

    # first page of the doc's last version
    first_page = db.get_first_page(db_session, last_ver.id)
    abs_thumbnail_path = plib.rel2abs(
        plib.thumbnail_path(first_page.id, size=size)
    )
    pdf_path = last_ver.abs_file_path

    logger.debug(f"Generating thumbnail for: doc_ver={last_ver}")
    logger.debug(f"pdf_path: {pdf_path}")
    logger.debug(f"output_folder: {abs_thumbnail_path.parent}, size={size}")
    image.generate_preview(
        pdf_path=pdf_path,
        output_folder=abs_thumbnail_path.parent,
        size=size
    )

    thumb_path = plib.thumbnail_path(first_page.id, size=size)
    logger.debug(f"thumb_path = {thumb_path}")
    return thumb_path


def doc_previews(doc_id: UUID):
    pass
