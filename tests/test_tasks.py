import uuid
from s3worker import tasks


def test_generate_page_image_task():
    uid = uuid.uuid4()
    tasks.generate_page_image_task(str(uid))
