"""
This module handles the interaction with the Google Drive API for uploading files.
"""
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build

class GoogleDriveService:
    """
    A wrapper class for the Google Drive API service.
    This will contain the low-level logic for API calls.
    
    """

    SCOPES = ['https://www.googleapis.com/auth/drive']
    SERVICE_ACCOUNT_FILE = 'credentials.json'


    def __init__(self, credentials=None):
        """Initializes the service."""
        try:
            creds = service_account.Credentials.from_service_account_file(
                self.SERVICE_ACCOUNT_FILE, scopes=self.SCOPES)
            self.service = build('drive', 'v3', credentials=creds)
            logging.info("Google Drive Service initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize Google Drive Service: {e}")
            # re-raise the exception to make it clear that initialization failed
            raise 

    def find_or_create_folder(self, folder_name, parent_folder_id=None):
        """
        Finds a folder by name inside a specific parent folder. 
        If it doesn't exist, creates it there. Returns the folder ID.
        """
        if not parent_folder_id:
            raise ValueError("parent_folder_id must be provided")

        # Search for a folder, specifying that it must be in the specified parent
        query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false and '{parent_folder_id}' in parents"
        response = self.service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        files = response.get('files', [])

        if files:
            folder_id = files[0].get('id')
            logging.info(f"Found existing folder '{folder_name}' inside parent.")
            return folder_id
        else:
            # 2. if not found, create new folder and specify path
            logging.info(f"Folder '{folder_name}' not found. Creating it inside parent {parent_folder_id}.")
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_folder_id]  # <-- ระบุตำแหน่งที่จะสร้าง
            }
            folder = self.service.files().create(body=file_metadata, fields='id').execute()
            folder_id = folder.get('id')
            logging.info(f"Created new folder '{folder_name}' with ID: {folder_id}")
            return folder_id

    def upload_file(self, file_name, file_content, folder_id):
        """
        Uploads a file with the given content into a specific folder.
        """
        # The real implementation will have API calls here.
        raise NotImplementedError("This method should be implemented in the real service.")


def upload_to_drive(service, file_name, file_content, destination_folder):
    """
    Orchestrates the process of uploading a file to a specific folder in Google Drive.

    Args:
        service: An instance of a Google Drive service wrapper.
        file_name (str): The name of the file to be saved.
        file_content (bytes): The binary content of the file.
        destination_folder (str): The name of the folder to save the file in.
    """
    # 1. Get the ID of the destination folder, creating it if necessary.
    folder_id = service.find_or_create_folder(destination_folder)
    
    # 2. Upload the file into that folder.
    service.upload_file(
        file_name=file_name,
        file_content=file_content,
        folder_id=folder_id
    )
    
    logging.info(
        "Successfully triggered upload for '%s' to folder '%s'.",
        file_name,
        destination_folder
    )