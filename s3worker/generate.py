import logging
from pathlib import Path
from uuid import UUID
from sqlalchemy.orm import Session

from . import db, image
from . import plib, config
from .types import ImagePreviewSize


settings = config.get_settings()

logger = logging.getLogger(__name__)

PREVIEW_IMAGE_MAP = {
    # size name        : size in pixels
    ImagePreviewSize.sm: settings.papermerge__preview__page_size_sm,
    ImagePreviewSize.md: settings.papermerge__preview__page_size_md,
    ImagePreviewSize.lg: settings.papermerge__preview__page_size_lg,
    ImagePreviewSize.xl: settings.papermerge__preview__page_size_xl,
}


def doc_thumbnail(
    db_session: Session,
    doc_id: UUID,
    size: ImagePreviewSize = settings.papermerge__thumbnail__size
) -> Path:
    logger.info(f"Generating thumbnail for doc_id={doc_id}")

    last_ver = db.get_last_version(db_session, doc_id)

    abs_thumbnail_path = plib.rel2abs(
        plib.thumbnail_path(doc_id, size=size)
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

    thumb_path = plib.thumbnail_path(doc_id, size=size)
    logger.debug(f"thumb_path = {thumb_path}")
    return thumb_path


def gen_page_preview(
    doc_ver_id,
    file_name: str,
    page_id: UUID,
    page_number: int,
    size: ImagePreviewSize
):
    logger.info(
        f"Generating preview for {page_id=} {page_number=} {size=}"
    )
    pdf_path = plib.abs_docver_path(
        str(doc_ver_id),
        str(file_name)
    )
    abs_image_path = plib.rel2abs(
        plib.page_preview_jpg_path(page_id, size=size)
    )
    image.generate_preview(
        pdf_path=pdf_path,
        output_folder=abs_image_path.parent,
        size=PREVIEW_IMAGE_MAP[size],
        page_number=page_number
    )

    return plib.page_preview_jpg_path(page_id, size=size)
