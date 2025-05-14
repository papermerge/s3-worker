from enum import Enum

DEFAULT_THUMBNAIL_SIZE = 100  # 100 pixels wide
DEFAULT_PAGE_SIZE = 900  # 900 pixels wide
JPG = 'jpg'
PAGES = 'pages'
THUMBNAILS = 'thumbnails'
DOCVERS = 'docvers'
OCR = 'ocr'
S3_WORKER_ADD_DOC_VER = 's3_worker_add_doc_vers'
S3_WORKER_REMOVE_DOC_VER = 's3_worker_remove_doc_vers'
S3_WORKER_REMOVE_DOC_THUMBNAIL = 's3_worker_remove_doc_thumbnail'
S3_WORKER_REMOVE_DOCS_THUMBNAIL = 's3_worker_remove_docs_thumbnail'
S3_WORKER_REMOVE_PAGE_THUMBNAIL = 's3_worker_remove_page_thumbnail'
S3_WORKER_GENERATE_PREVIEW = 's3_worker_generate_preview'
# generate document thumbnail preview i.e. one single image
# as preview for the whole document
S3_WORKER_GENERATE_DOC_THUMBNAIL = "s3_worker_generate_doc_thumbnail"
# generate preview image(s) for one or multiple document pages
S3_WORKER_GENERATE_PAGE_IMAGE = "s3_worker_generate_page_image"


class ImagePreviewStatus(Enum):
    """Image preview status

    1. If database field `preview_status` is NULL ->
        image preview was not considered yet i.e. client
        have not asked for it yet.
    2. "pending" - image preview was scheduled, as client has asked
        for it, but has not started yet
    3. "ready - image preview complete:
        a. preview image was generated
        b. preview image was uploaded to S3
    4. "failed" image preview failed
    """
    READY = "ready"
    PENDING = "pending"
    FAILED = "failed"
