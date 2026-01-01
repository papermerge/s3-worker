from uuid import UUID
import typer
import logging
from typing_extensions import Annotated

from pathlib import Path
from rich.progress import track
from rich import print_json
from rich import print

from s3worker.db.engine import Session
from s3worker import client, generate, db, utils, config, schemas


logger = logging.getLogger(__name__)
app = typer.Typer(help="S3/R2 Worker CLI - supports both AWS S3 and Cloudflare R2")
settings = config.get_settings()

utils.setup_logging(settings.pm_log_config)

TargetPath = Annotated[
    Path,
    typer.Argument(help="File or folder to be uploaded")
]

KeynamePath = Annotated[
    Path,
    typer.Argument(help="This arguments ends up as storage keyname")
]

KeynamesPath = Annotated[
    list[Path],
    typer.Argument(help="One or multiple storage object keys")
]


@app.command()
def upload(target: TargetPath, keyname: KeynamePath):
    """Upload a file to S3/R2 bucket"""
    client.upload(target, keyname)


@app.command()
def add_doc_vers(uids: list[str]):
    """Add document versions to storage"""
    client.add_doc_vers(uids)


@app.command()
def remove_doc_vers(uids: list[str]):
    """Remove document versions from storage"""
    client.remove_doc_vers(uids)


@app.command()
def delete(keynames: KeynamesPath):
    """Delete objects from storage"""
    client.delete(keynames)


@app.command()
def doc_thumbnail(doc_id: str):
    """Generate thumbnail for the document

    Thumbnails is generated for the first page of the last version
    of the document identified with given UUID
    """
    with Session() as db_session:
        thumb_path: Path = generate.doc_thumbnail(db_session, UUID(doc_id))
        client.upload_file(thumb_path)


@app.command()
def sync():
    """Uploads all local media data to S3/R2

    Iterates through all local media files and checks if they
    are present on storage. If not present - upload, otherwise continue.
    All uploaded objects will be prefixed with `pm_prefix`.
    """
    backend = client.get_storage_backend_name()
    print(f"[bold green]Starting sync to {backend}...[/bold green]")
    client.sync()
    print("[bold green]Sync complete![/bold green]")


@app.command()
def generate_doc_thumbnails(progress: bool = False):
    """Generate thumbnails for all documents and if the
     previews are not present on storage - upload them"""
    prefix = settings.pm_prefix
    bucket_name = settings.pm_s3_bucket_name

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


@app.command()
def presigned_url(
    key: Annotated[str, typer.Argument(help="Object key in the bucket")],
    expires: Annotated[int, typer.Option(help="URL expiration in seconds")] = 3600
):
    """Generate a presigned URL for an object"""
    url = client.generate_presigned_url(key, expires_in=expires)
    print(f"[bold green]Presigned URL:[/bold green]")
    print(url)


@app.command()
def info():
    """Show storage configuration info"""
    backend = client.get_storage_backend_name()
    print(f"[bold]Storage Configuration ({backend}):[/bold]")
    print(f"  Backend: {settings.pm_storage_backend.value}")
    print(f"  Bucket: {settings.pm_s3_bucket_name}")
    
    if settings.pm_storage_backend == config.StorageBackend.AWS:
        print(f"  Region: {settings.aws_region_name or '(default)'}")
        if settings.aws_access_key_id:
            print(f"  Access Key: {settings.aws_access_key_id[:8]}...")
        else:
            print("  Access Key: (not set)")
    else:
        if settings.r2_account_id:
            print(f"  Account ID: {settings.r2_account_id[:8]}...")
        else:
            print("  Account ID: (not set)")
        print(f"  Endpoint: {settings.r2_endpoint_url}")
        if settings.r2_access_key_id:
            print(f"  Access Key: {settings.r2_access_key_id[:8]}...")
        else:
            print("  Access Key: (not set)")
    
    print(f"  Prefix: {settings.pm_prefix or '(none)'}")
    print(f"  Media Root: {settings.pm_media_root}")


@app.command(name="config")
def print_config_cmd():
    """Print config settings as JSON"""
    print_json(settings.model_dump_json())
