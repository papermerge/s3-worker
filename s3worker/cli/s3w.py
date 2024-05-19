from uuid import UUID
import typer
from typing_extensions import Annotated
from pathlib import Path

from s3worker import client, generate

app = typer.Typer(help="Groups basic management")

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
    thumb_base = generate.doc_thumbnail(UUID(doc_id))
    client.upload_doc_thumbnail(thumb_base)
