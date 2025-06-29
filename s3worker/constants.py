from enum import Enum

INBOX_TITLE = "inbox"
HOME_TITLE = "home"
CTYPE_FOLDER = "folder"
CTYPE_DOCUMENT = "document"

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

