import uuid
from uuid import UUID
from pydantic import (BaseModel, ConfigDict, Field)

from s3worker import plib, types


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


class Resource(BaseModel):
    type: types.ResourceType
    id: uuid.UUID


class NodeResource(Resource):
    type: types.ResourceType = types.ResourceType.NODE


class Owner(BaseModel):
    owner_type: types.OwnerType
    owner_id: uuid.UUID

    @staticmethod
    def create_from(
        user_id: uuid.UUID | None = None,
        group_id: uuid.UUID | None = None
    ) -> "Owner":
        if group_id is not None:
            return Owner(owner_type=types.OwnerType.GROUP, owner_id=group_id)
        elif user_id is not None:
            return Owner(owner_type=types.OwnerType.USER, owner_id=user_id)
        else:
            raise ValueError("Either user_id or group_id must be provided")
