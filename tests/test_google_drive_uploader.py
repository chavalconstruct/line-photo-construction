from unittest.mock import MagicMock, patch
import pytest

from src.google_drive_uploader import GoogleDriveService

# เราจะเพิ่ม patch สำหรับ os.getenv เพื่อควบคุมสภาพแวดล้อมของเทสต์
@patch('src.google_drive_uploader.os.getenv')
@patch('src.google_drive_uploader.GoogleDriveService._get_credentials')
@patch('src.google_drive_uploader.build')
def test_find_or_create_folder_when_folder_exists(mock_build, mock_get_credentials, mock_getenv):
    """
    Tests that if a folder is found, its ID is returned 
    and no new folder is created.
    """
    # ทำให้ getenv คืนค่า None เพื่อไม่ให้เข้าเงื่อนไข 'production'
    mock_getenv.return_value = None
    
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.files.return_value.list.return_value.execute.return_value = {
        'files': [{'id': 'existing_folder_id'}]
    }
    mock_get_credentials.return_value = MagicMock()

    google_drive_service = GoogleDriveService()
    folder_id = google_drive_service.find_or_create_folder('My-Existing-Folder')

    assert folder_id == 'existing_folder_id'
    mock_service.files.return_value.list.assert_called_once()
    mock_service.files.return_value.create.assert_not_called()

@patch('src.google_drive_uploader.os.getenv')
@patch('src.google_drive_uploader.GoogleDriveService._get_credentials')
@patch('src.google_drive_uploader.build')
def test_find_or_create_folder_when_folder_does_not_exist(mock_build, mock_get_credentials, mock_getenv):
    """
    Tests that if a folder is not found, a new one is created 
    and its ID is returned.
    """
    mock_getenv.return_value = None

    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.files.return_value.list.return_value.execute.return_value = {
        'files': []
    }
    mock_service.files.return_value.create.return_value.execute.return_value = {
        'id': 'a_newly_created_id'
    }
    mock_get_credentials.return_value = MagicMock()

    google_drive_service = GoogleDriveService()
    folder_id = google_drive_service.find_or_create_folder('My-New-Folder')

    assert folder_id == 'a_newly_created_id'
    mock_service.files.return_value.list.assert_called_once()
    mock_service.files.return_value.create.assert_called_once()

@patch('src.google_drive_uploader.os.getenv')
@patch('src.google_drive_uploader.MediaIoBaseUpload')
@patch('src.google_drive_uploader.GoogleDriveService._get_credentials')
@patch('src.google_drive_uploader.build')
def test_upload_file_calls_api_with_correct_parameters(mock_build, mock_get_credentials, mock_media_io, mock_getenv):
    """
    Tests that the upload_file method calls the Google Drive API's 'create'
    method with the correct metadata and media body.
    """
    mock_getenv.return_value = None

    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_get_credentials.return_value = MagicMock()
    mock_request = MagicMock()
    mock_service.files.return_value.create.return_value = mock_request
    mock_request.next_chunk.return_value = (None, {'id': 'uploaded_file_id'})

    file_name = 'test_image.jpg'
    file_content = b'this is dummy image content'
    folder_id = 'some_folder_id'
    
    google_drive_service = GoogleDriveService()
    file_id = google_drive_service.upload_file(file_name, file_content, folder_id)

    assert file_id == 'uploaded_file_id'
    mock_media_io.assert_called_once()
    
    expected_metadata = {'name': file_name, 'parents': [folder_id]}
    
    mock_service.files.return_value.create.assert_called_once_with(
        body=expected_metadata,
        media_body=mock_media_io.return_value,
        fields='id'
    )