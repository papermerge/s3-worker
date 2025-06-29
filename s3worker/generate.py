import logging
from pathlib import Path
from uuid import UUID
from sqlalchemy.orm import Session

from . import db, image
from . import plib, config
from .types import ImagePreviewSize


settings = config.get_settings()

logger = logging.getLogger(__name__)


def doc_thumbnail(
    db_session: Session,
    doc_id: UUID,
    size_px: int = settings.papermerge__thumbnail__size
) -> Path:
    logger.info(f"Generating thumbnail for doc_id={doc_id}")

    last_ver = db.get_last_version(db_session, doc_id)

    abs_thumbnail_path = plib.rel2abs(
        plib.thumbnail_path(doc_id, size=ImagePreviewSize.sm)
    )
    pdf_path = last_ver.abs_file_path

    logger.debug(f"Generating thumbnail for: doc_ver={last_ver}")
    logger.debug(f"pdf_path: {pdf_path}")
    logger.debug(f"output_folder: {abs_thumbnail_path.parent}, size_px={size_px}")
    image.generate_preview(
        pdf_path=pdf_path,
        output_folder=abs_thumbnail_path.parent,
        size_px=size_px,
        size_name="sm"
    )

    thumb_path = plib.thumbnail_path(doc_id, size=ImagePreviewSize.sm)
    logger.debug(f"thumb_path = {thumb_path}")
    return thumb_path
