import typer
from typing_extensions import Annotated
from pathlib import Path

from s3worker import client

app = typer.Typer(help="Groups basic management")


@app.command()
def upload(file_target: str, object_path: str):
    client.upload(file_target, object_path)
