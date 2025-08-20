import unittest
from unittest.mock import patch, MagicMock

# This will fail at first because the file and function don't exist yet!
from src.google_drive_uploader import upload_to_drive

class TestGoogleDriveUploader(unittest.TestCase):
    """
    Test suite for the Google Drive uploader functionality.
    """

    @patch('src.google_drive_uploader.GoogleDriveService')
    def test_upload_to_drive_calls_service_correctly(self, MockGoogleDriveService):
        """
        Ensures that the upload_to_drive function interacts with the
        Google Drive service as expected for a new file and folder.
        """
        # 1. Setup
        # Create a mock instance of our Google Drive service wrapper
        mock_service_instance = MockGoogleDriveService.return_value
        mock_service_instance.find_or_create_folder.return_value = 'mock_folder_id_123'

        image_content = b'dummy image bytes'
        file_name = 'test_image.jpg'
        destination_folder = 'Group A'

        # 2. Action
        # Call the function we are testing (which doesn't exist yet)
        upload_to_drive(
            service=mock_service_instance,
            file_name=file_name,
            file_content=image_content,
            destination_folder=destination_folder
        )

        # 3. Assert
        # Verify that our service methods were called with the correct arguments
        mock_service_instance.find_or_create_folder.assert_called_once_with('Group A')
        mock_service_instance.upload_file.assert_called_once_with(
            file_name='test_image.jpg',
            file_content=b'dummy image bytes',
            folder_id='mock_folder_id_123'
        )