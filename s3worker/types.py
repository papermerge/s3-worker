from enum import Enum


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
