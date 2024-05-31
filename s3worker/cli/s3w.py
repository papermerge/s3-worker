from uuid import UUID
import typer
from typing_extensions import Annotated

from pathlib import Path
from rich.progress import track

from s3worker import client, generate, db, utils, config, schemas


app = typer.Typer(help="Groups basic management")
settings = config.get_settings()

utils.setup_logging(settings.papermerge__main__logging_cfg)

TargetPath = Annotated[
    Path,
    typer.Argument(help="File or folder to be uploaded")
]

KeynamePath = Annotated[
    Path,
    typer.Argument(help="This arguments ends up as s3 keyname")
]

KeynamesPath = Annotated[
    list[Path],
    typer.Argument(help="One or multiple s3 object keys")
]


@app.command()
def upload(target: TargetPath, keyname: KeynamePath):
    client.upload(target, keyname)


@app.command()
def add_doc_vers(uids: list[str]):
    client.add_doc_vers(uids)


@app.command()
def remove_doc_vers(uids: list[str]):
    client.remove_doc_vers(uids)


@app.command()
def delete(keynames: KeynamesPath):
    client.delete(keynames)


@app.command()
def doc_thumbnail(doc_id: str):
    """Generate thumbnail for the document

    Thumbnails is generated for the first page of the last version
    of the document identified with given UUID
    """
    Session = db.get_db()
    with Session() as db_session:
        thumb_path: Path = generate.doc_thumbnail(db_session, UUID(doc_id))
        client.upload_file(thumb_path)


@app.command()
def sync():
    """Uploads all local media data to S3

    Iterates through all local media files and checks if they
    are present on S3. If not present - upload, otherwise continue.
    What is important, is that all uploaded objects will be prefixed with
    `papermerge__s3__object_prefix` (this
    """
    client.sync()


@app.command()
def generate_previews(progress: bool = False):
    """Generate doc/pages previews and if necessary uploads them to S3"""
    Session = db.get_db()
    prefix = settings.papermerge__s3__object_prefix
    bucket_name = settings.papermerge__s3__bucket_name

    with Session() as db_session:
        all_docs: list[schemas.Document] = db.get_docs(db_session)

        if progress:
            all_items = track(all_docs, description="Generating...")
        else:
            all_items = all_docs

        for doc in all_items:
            thumb_path: Path = generate.doc_thumbnail(db_session, doc.id)
            keyname = prefix / thumb_path
            if not client.s3_obj_exists(
                bucket_name=bucket_name,
                keyname=str(keyname)
            ):
                client.upload_file(thumb_path)

            file_paths = generate.doc_previews(db_session, doc.id)
            for file_path in file_paths:
                if not client.s3_obj_exists(
                    bucket_name=bucket_name,
                    keyname=str(keyname)
                ):
                    client.upload_file(file_path)
