# Changelog


## [0.5] - not yet released

- add `generate_doc_thumbnail_task` to generate document thumbnails. It also
    updates documents `preview_status` attribute (None, PENDING, READY, FAILED).
- add `generate_page_image_task` to generate page images (in sm, md, lg and xl sizes)
- add unit tests to s3worker project
- add CI tests pipeline to the project
- adopt poetry 2.1 format for pyproject.toml file 