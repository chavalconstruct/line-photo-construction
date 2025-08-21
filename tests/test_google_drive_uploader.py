from unittest.mock import MagicMock, patch
import pytest

from src.google_drive_uploader import GoogleDriveService

# The @patch decorator intercepts the 'build' function from googleapiclient.discovery
# right where it's used inside our GoogleDriveService class.
# We also mock '_get_credentials' to prevent any real authentication attempts.
@patch('src.google_drive_uploader.GoogleDriveService._get_credentials')
@patch('src.google_drive_uploader.build')
def test_find_or_create_folder_when_folder_exists(mock_build, mock_get_credentials):
    """
    Tests that if a folder is found, its ID is returned 
    and no new folder is created.
    """
    # Arrange: Configure the mock to simulate the API's behavior.
    # We create a mock for the entire service object chain.
    mock_service = MagicMock()
    mock_build.return_value = mock_service

    # Simulate the API response when a folder is found.
    # The 'list' method is called, and its 'execute' returns a list with the folder.
    mock_service.files.return_value.list.return_value.execute.return_value = {
        'files': [{'id': 'existing_folder_id'}]
    }
    
    # We need a dummy credentials object for the constructor
    mock_get_credentials.return_value = MagicMock()

    # Act: Instantiate our service and call the method we are testing.
    google_drive_service = GoogleDriveService()
    folder_id = google_drive_service.find_or_create_folder('My-Existing-Folder')

    # Assert: Verify that our code behaved as expected.
    # 1. Check if the correct folder ID was returned.
    assert folder_id == 'existing_folder_id'

    # 2. Verify that the 'list' method was called correctly.
    mock_service.files.return_value.list.assert_called_once()
    
    # 3. CRUCIAL: Verify that the 'create' method was NOT called.
    mock_service.files.return_value.create.assert_not_called()

@patch('src.google_drive_uploader.GoogleDriveService._get_credentials')
@patch('src.google_drive_uploader.build')
def test_find_or_create_folder_when_folder_does_not_exist(mock_build, mock_get_credentials):
    """
    Tests that if a folder is not found, a new one is created 
    and its ID is returned.
    """
    # Arrange: Configure the mock for this specific scenario.
    mock_service = MagicMock()
    mock_build.return_value = mock_service

    # 1. Simulate the 'list' call finding NOTHING.
    mock_service.files.return_value.list.return_value.execute.return_value = {
        'files': []  # <-- Key difference: return an empty list
    }

    # 2. Simulate the 'create' call returning a new folder ID.
    mock_service.files.return_value.create.return_value.execute.return_value = {
        'id': 'a_newly_created_id'
    }

    mock_get_credentials.return_value = MagicMock()

    # Act: Call the method under test.
    google_drive_service = GoogleDriveService()
    folder_id = google_drive_service.find_or_create_folder('My-New-Folder')

    # Assert: Verify the behavior is correct.
    # 1. Check that the new folder's ID was returned.
    assert folder_id == 'a_newly_created_id'

    # 2. Verify that 'list' was called to search first.
    mock_service.files.return_value.list.assert_called_once()
    
    # 3. CRUCIAL: Verify that 'create' was called because the folder was not found.
    mock_service.files.return_value.create.assert_called_once()

# We add a new patch for MediaIoBaseUpload to control its creation
@patch('src.google_drive_uploader.MediaIoBaseUpload')
@patch('src.google_drive_uploader.GoogleDriveService._get_credentials')
@patch('src.google_drive_uploader.build')
def test_upload_file_calls_api_with_correct_parameters(mock_build, mock_get_credentials, mock_media_io):
    """
    Tests that the upload_file method calls the Google Drive API's 'create'
    method with the correct metadata and media body.
    """
    # Arrange
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_get_credentials.return_value = MagicMock()

    # We need to mock the chained calls for the resumable upload part
    mock_request = MagicMock()
    mock_service.files.return_value.create.return_value = mock_request
    mock_request.next_chunk.return_value = (None, {'id': 'uploaded_file_id'}) # Simulate upload completion

    # Dummy data for the test
    file_name = 'test_image.jpg'
    file_content = b'this is dummy image content'
    folder_id = 'some_folder_id'
    
    # Act
    google_drive_service = GoogleDriveService()
    file_id = google_drive_service.upload_file(file_name, file_content, folder_id)

    # Assert
    # 1. Verify that the returned ID is correct.
    assert file_id == 'uploaded_file_id'

    # 2. Verify that MediaIoBaseUpload was instantiated correctly.
    # We check that it was called with content (wrapped in BytesIO) and the correct mimetype.
    # Note: We can't directly compare BytesIO objects, so we check the call count.
    mock_media_io.assert_called_once()
    # To be more specific, you could inspect args: mock_media_io.call_args[1]['mimetype'] == 'image/jpeg'

    # 3. CRUCIAL: Verify that the 'create' method was called with the correct arguments.
    expected_metadata = {'name': file_name, 'parents': [folder_id]}
    
    mock_service.files.return_value.create.assert_called_once_with(
        body=expected_metadata,
        media_body=mock_media_io.return_value, # Check that the created media object was passed
        fields='id'
    )