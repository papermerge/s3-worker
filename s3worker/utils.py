import logging
import uuid
import yaml
from pathlib import Path
from logging.config import dictConfig

from s3worker.db.engine import Session
from s3worker import exc, types, db, client, plib
from s3worker.config import get_settings

logger = logging.getLogger(__name__)


def get_filename_in_dir(dir: Path) -> str | None:
    """Returns FIRST filename from the list of files found in given directory

    Document versions are stored in following format:
    ```
        /<media-root>/<prefix>/ab/cd/abcd12c...a/<file-name>.<ext>

    Where abcd12c...a is the UUID of the document version.
    This method returns the <file-name>.<ext> part - which is assumed
    to be the only file in the directory.
    ```
    """
    results = dir.glob('*', case_sensitive=False)
    for item in results:
        # it is the only file in the directory
        return item.name

    return None


def setup_logging(config: Path):
    if config is None:
        return

    with open(config, 'r') as stream:
        config = yaml.load(stream, Loader=yaml.FullLoader)

    dictConfig(config)


def make_sure_file_exists_for(
    doc_id: uuid.UUID,
    docver_id: uuid.UUID,
    file_name: str,
) -> bool:
    """
    Returns True if the given file exists for the given document version
    Returns False otherwise
    """
    original_path = plib.abs_docver_path(docver_id, file_name)
    if original_path.exists():
        return True

    settings = get_settings()
    if settings.storage_backend == types.StorageBackend.LOCAL:
        return False

    # At this point
    # 1. Storage backage is either R2 or S3
    # 2. There is no local copy of the file

    try:
        # try to retrieve local copy of the file from remove copy of Obj Storage
        client.download_docver(
            docver_id=docver_id,
            file_name=file_name
        )
    except exc.S3DocumentNotFound as e:
        logger.error(f"Document not found in storage: {e}")
        with Session() as db_session:
            db.update_document_processing_status(
                db_session,
                doc_id,
                status=types.DocumentProcessingStatus.failed.value,
                error=f"File not found in storage: {str(e)}"
            )
        return False

    if original_path.exists():
        return True

    return False
