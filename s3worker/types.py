from enum import Enum


class DocumentProcessingStatus(str, Enum):
    """Document processing status
    
    Tracks the lifecycle of document processing after upload:
    
    1. "uploaded" - File uploaded to storage, document record created
    2. "converting" - Converting image to PDF (for non-PDF uploads)
    3. "processing_pages" - Counting pages, creating page records
    4. "ready" - All processing complete, document ready for use
    5. "failed" - Processing failed, see processing_error for details
    """
    uploaded = "uploaded"
    converting = "converting"
    processing_pages = "processing_pages"
    ready = "ready"
    failed = "failed"


class MimeType(str, Enum):
    """Supported MIME types for documents"""
    application_pdf = "application/pdf"
    image_jpeg = "image/jpeg"
    image_png = "image/png"
    image_tiff = "image/tiff"


class ImagePreviewStatus(str, Enum):
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
    ready = "ready"
    pending = "pending"
    failed = "failed"


class ImagePreviewSize(str, Enum):
    sm = "sm"  # small
    md = "md"  # medium
    lg = "lg"  # large
    xl = "xl"  # extra large
