from uuid import UUID
import typer
from typing_extensions import Annotated

from pathlib import Path

from s3worker import client, generate, db, utils, config


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
