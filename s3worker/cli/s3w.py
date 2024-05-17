import typer
from typing_extensions import Annotated
from pathlib import Path

from s3worker import client

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
def delete(keynames: KeynamesPath):
    client.delete(keynames)
