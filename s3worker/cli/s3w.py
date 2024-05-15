import typer
from pathlib import Path

from s3worker import client

app = typer.Typer(help="Groups basic management")


@app.command()
def upload(file: Path):
    client.upload(file)
