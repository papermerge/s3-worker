from uuid import UUID
from pydantic import (BaseModel, ConfigDict, Field)

from s3worker import plib


class Page(BaseModel):
    id: UUID
    number: int
    document_version_id: UUID

    # Config
    model_config = ConfigDict(from_attributes=True)


class DocumentVersion(BaseModel):
    id: UUID
    number: int
    file_name: str | None = None
    size: int = 0
    page_count: int = 0
    document_id: UUID
    pages: list[Page] = []

    # Config
    model_config = ConfigDict(from_attributes=True)

    @property
    def abs_file_path(self):
        return plib.abs_docver_path(
            str(self.id),
            str(self.file_name)
        )


class Document(BaseModel):
    id: UUID
    versions: list[DocumentVersion] = []

    # Config
    model_config = ConfigDict(from_attributes=True)
