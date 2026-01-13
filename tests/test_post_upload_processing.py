from pathlib import Path
from unittest import mock
import pytest

from s3worker.db import orm
from s3worker.db.post_upload_processing import (
    process_pdf_document,
    process_non_pdf_document
)
from s3worker.types import DocumentProcessingStatus, MimeType
from sqlalchemy import select


# Tests for process_pdf_document


@mock.patch('s3worker.db.post_upload_processing.utils.make_sure_file_exists_for')
@mock.patch('s3worker.db.post_upload_processing.plib.abs_docver_path')
@mock.patch('s3worker.db.post_upload_processing.get_page_count')
def test_process_pdf_document_success(
    mock_get_page_count,
    mock_abs_path,
    mock_make_sure_file,
    db_session,
    pdf_document_with_version
):
    """Test successful PDF document processing"""
    # Setup
    document, version = pdf_document_with_version
    doc_id = document.id
    ver_id = version.id
    lang = "eng"

    mock_make_sure_file.return_value = True
    mock_abs_path.return_value = Path("/tmp/test.pdf")

    mock_get_page_count.return_value = 3

    # Execute
    process_pdf_document(
        db_session,
        doc_id,
        ver_id,
        lang,
        version
    )

    # Assert - query fresh objects from the database
    stmt = select(orm.Document).where(orm.Document.id == doc_id)
    updated_document = db_session.execute(stmt).scalar_one()
    assert updated_document.processing_status == DocumentProcessingStatus.ready.value

    # Check that version page count is updated
    stmt = select(orm.DocumentVersion).where(orm.DocumentVersion.id == ver_id)
    updated_version = db_session.execute(stmt).scalar_one()
    assert updated_version.page_count == 3

    # Check that pages were created
    stmt = select(orm.Page).where(orm.Page.document_version_id == ver_id)
    pages = db_session.execute(stmt).scalars().all()
    assert len(pages) == 3

    # Check file operations
    mock_make_sure_file.assert_called_once_with(
        doc_id=doc_id,
        docver_id=ver_id,
        file_name=version.file_name
    )



@mock.patch('s3worker.db.post_upload_processing.utils.make_sure_file_exists_for')
@mock.patch('s3worker.db.post_upload_processing.plib.abs_docver_path')
@mock.patch('s3worker.db.post_upload_processing.img2pdf.convert')
@mock.patch('s3worker.db.post_upload_processing.Pdf')
@mock.patch('s3worker.db.post_upload_processing.client.get_client')
@mock.patch('s3worker.db.post_upload_processing.client.add_doc_ver')
@mock.patch('s3worker.db.post_upload_processing.settings')
@mock.patch('builtins.open', new_callable=mock.mock_open)
def test_process_non_pdf_document_success_local_storage(
    mock_open_builtin,
    mock_settings,
    mock_add_doc_ver,
    mock_get_client,
    mock_pdf_class,
    mock_img2pdf_convert,
    mock_abs_path,
    mock_make_sure_file,
    db_session,
    system_user,
    image_document_with_version,
    mock_pdf_file
):
    """Test successful image document processing with local storage"""
    # Setup
    document, version = image_document_with_version
    doc_id = document.id
    ver_id = version.id
    user_id = system_user.id
    lang = "eng"

    mock_make_sure_file.return_value = True

    # Create a side_effect function that returns different paths
    def abs_path_side_effect(ver_id_arg, filename):
        return Path(f"/tmp/{filename}")

    mock_abs_path.side_effect = abs_path_side_effect
    mock_img2pdf_convert.return_value = b"fake_pdf_bytes"
    mock_pdf_class.open.return_value = mock_pdf_file

    # Mock settings for local storage
    from s3worker.types import StorageBackend
    mock_settings.storage_backend = StorageBackend.LOCAL

    # Execute
    process_non_pdf_document(
        db_session,
        doc_id,
        ver_id,
        user_id,
        lang,
        version
    )

    # Assert - query fresh objects from the database
    stmt = select(orm.Document).where(orm.Document.id == doc_id)
    updated_document = db_session.execute(stmt).scalar_one()
    assert updated_document.processing_status == DocumentProcessingStatus.ready.value

    # Check that original version page count is updated
    stmt = select(orm.DocumentVersion).where(orm.DocumentVersion.id == ver_id)
    updated_version = db_session.execute(stmt).scalar_one()
    assert updated_version.page_count == 3

    # Check that a new PDF version was created
    stmt = select(orm.DocumentVersion).where(
        orm.DocumentVersion.document_id == doc_id
    ).order_by(orm.DocumentVersion.number.desc())

    versions = db_session.execute(stmt).scalars().all()
    assert len(versions) == 2

    pdf_version = versions[0]
    assert pdf_version.mime_type == MimeType.application_pdf.value
    assert pdf_version.file_name.endswith('.pdf')

    # Check that pages were created for both versions
    stmt = select(orm.Page).where(orm.Page.document_version_id == ver_id)
    original_pages = db_session.execute(stmt).scalars().all()
    assert len(original_pages) == 3

    stmt = select(orm.Page).where(orm.Page.document_version_id == pdf_version.id)
    pdf_pages = db_session.execute(stmt).scalars().all()
    assert len(pdf_pages) == 3



@mock.patch('s3worker.db.post_upload_processing.utils.make_sure_file_exists_for')
@mock.patch('s3worker.db.post_upload_processing.plib.abs_docver_path')
@mock.patch('s3worker.db.post_upload_processing.img2pdf.convert')
@mock.patch('s3worker.db.post_upload_processing.Pdf')
@mock.patch('s3worker.db.post_upload_processing.client.get_client')
@mock.patch('s3worker.db.post_upload_processing.client.add_doc_ver')
@mock.patch('s3worker.db.post_upload_processing.settings')
@mock.patch('builtins.open', new_callable=mock.mock_open)
def test_process_non_pdf_document_success_s3_storage(
    mock_open_builtin,
    mock_settings,
    mock_add_doc_ver,
    mock_get_client,
    mock_pdf_class,
    mock_img2pdf_convert,
    mock_abs_path,
    mock_make_sure_file,
    db_session,
    system_user,
    image_document_with_version,
    mock_pdf_file
):
    """Test successful image document processing with S3 storage"""
    # Setup
    document, version = image_document_with_version
    doc_id = document.id
    ver_id = version.id
    user_id = system_user.id
    lang = "eng"

    mock_make_sure_file.return_value = True

    def abs_path_side_effect(ver_id_arg, filename):
        return Path(f"/tmp/{filename}")

    mock_abs_path.side_effect = abs_path_side_effect
    mock_img2pdf_convert.return_value = b"fake_pdf_bytes"
    mock_pdf_class.open.return_value = mock_pdf_file

    # Mock settings for S3 storage
    from s3worker.types import StorageBackend
    mock_settings.storage_backend = StorageBackend.S3

    # Mock S3 client
    mock_s3_client = mock.MagicMock()
    mock_get_client.return_value = mock_s3_client

    # Execute
    process_non_pdf_document(
        db_session,
        doc_id,
        ver_id,
        user_id,
        lang,
        version
    )

    # Get the actual PDF version ID that was created
    stmt = select(orm.DocumentVersion).where(
        orm.DocumentVersion.document_id == doc_id
    ).order_by(orm.DocumentVersion.number.desc())
    versions = db_session.execute(stmt).scalars().all()
    assert len(versions) == 2



@mock.patch('s3worker.db.post_upload_processing.utils.make_sure_file_exists_for')
@mock.patch('s3worker.db.post_upload_processing.plib.abs_docver_path')
@mock.patch('s3worker.db.post_upload_processing.img2pdf.convert')
@mock.patch('s3worker.db.post_upload_processing.logger')
@mock.patch('builtins.open', new_callable=mock.mock_open)
def test_process_non_pdf_document_conversion_error(
    mock_open_builtin,
    mock_logger,
    mock_img2pdf_convert,
    mock_abs_path,
    mock_make_sure_file,
    db_session,
    image_document_with_version
):
    """Test image processing when conversion fails"""
    # Setup
    document, version = image_document_with_version
    doc_id = document.id
    ver_id = version.id
    user_id = document.created_by
    lang = "eng"

    mock_make_sure_file.return_value = True
    mock_abs_path.return_value = Path("/tmp/test.png")

    # Mock img2pdf to raise ImageOpenError
    from img2pdf import ImageOpenError
    mock_img2pdf_convert.side_effect = ImageOpenError("Invalid image")

    # Execute
    process_non_pdf_document(
        db_session,
        doc_id,
        ver_id,
        user_id,
        lang,
        version
    )

    # Assert
    mock_logger.error.assert_called()
    error_message = mock_logger.error.call_args[0][0]
    assert "Image conversion failed" in error_message

    # Check status was updated to failed
    stmt = select(orm.Document).where(orm.Document.id == doc_id)
    updated_document = db_session.execute(stmt).scalar_one()
    assert updated_document.processing_status == DocumentProcessingStatus.failed.value
    assert "Image conversion failed" in updated_document.processing_error


@mock.patch('s3worker.db.post_upload_processing.utils.make_sure_file_exists_for')
@mock.patch('s3worker.db.post_upload_processing.plib.abs_docver_path')
@mock.patch('s3worker.db.post_upload_processing.img2pdf.convert')
@mock.patch('s3worker.db.post_upload_processing.logger')
@mock.patch('builtins.open', new_callable=mock.mock_open)
def test_process_non_pdf_document_unexpected_error(
    mock_open_builtin,
    mock_logger,
    mock_img2pdf_convert,
    mock_abs_path,
    mock_make_sure_file,
    db_session,
    image_document_with_version
):
    """Test image processing when unexpected error occurs"""
    # Setup
    document, version = image_document_with_version
    doc_id = document.id
    ver_id = version.id
    user_id = document.created_by
    lang = "eng"

    mock_make_sure_file.return_value = True
    mock_abs_path.return_value = Path("/tmp/test.png")

    # Mock img2pdf to raise a generic exception
    mock_img2pdf_convert.side_effect = RuntimeError("Unexpected error")

    # Execute and expect exception to be raised
    with pytest.raises(RuntimeError):
        process_non_pdf_document(
            db_session,
            doc_id,
            ver_id,
            user_id,
            lang,
            version
        )

    # Assert
    mock_logger.error.assert_called()
    error_message = mock_logger.error.call_args[0][0]
    assert "Unexpected error during image processing" in error_message

    # Check status was updated to failed
    stmt = select(orm.Document).where(orm.Document.id == doc_id)
    updated_document = db_session.execute(stmt).scalar_one()
    assert updated_document.processing_status == DocumentProcessingStatus.failed.value
    assert "Processing failed" in updated_document.processing_error
