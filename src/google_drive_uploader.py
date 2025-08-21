"""
This module handles the interaction with the Google Drive API for uploading files.
"""
import logging
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

class GoogleDriveService:
    """
    A wrapper class for the Google Drive API service.
    This contains the real implementation for API calls.
    """
    SCOPES = ['https://www.googleapis.com/auth/drive']
    SERVICE_ACCOUNT_FILE = 'credentials.json'

    def __init__(self):
        """Initializes the service."""
        try:
            creds = service_account.Credentials.from_service_account_file(
                self.SERVICE_ACCOUNT_FILE, scopes=self.SCOPES)
            self.service = build('drive', 'v3', credentials=creds)
            logging.info("Google Drive Service initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize Google Drive Service: {e}")
            raise

    def find_or_create_folder(self, folder_name, parent_folder_id=None):
        """
        Finds a folder by name inside a specific parent folder.
        If it doesn't exist, creates it there. Returns the folder ID.
        """
        if not parent_folder_id:
            raise ValueError("parent_folder_id must be provided")

        query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false and '{parent_folder_id}' in parents"
        response = self.service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)',
            # Add these two lines to search in Shared Drives
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        files = response.get('files', [])

        if files:
            folder_id = files[0].get('id')
            logging.info(f"Found existing folder '{folder_name}' inside parent.")
            return folder_id
        else:
            logging.info(f"Folder '{folder_name}' not found. Creating it inside parent {parent_folder_id}.")
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_folder_id]
            }
            folder = self.service.files().create(
                body=file_metadata, 
                fields='id',
                # Add this line to allow creation in a Shared Drive
                supportsAllDrives=True
            ).execute()
            logging.info(f"Created new folder '{folder_name}' with ID: {folder_id}")
            return folder.get('id')

    def upload_file(self, file_name, file_content, folder_id):
        """
        Uploads a file with the given content to a specific folder.
        
        Args:
            file_name (str): The desired name of the file in Google Drive.
            file_content (bytes): The binary content of the file.
            folder_id (str): The ID of the parent folder to upload into.
        """
        file_metadata = {'name': file_name, 'parents': [folder_id]}
        
        # Treat the bytes content as a file for the upload
        media = MediaIoBaseUpload(
            io.BytesIO(file_content), 
            mimetype='image/jpeg',  # Assuming images for now
            resumable=True
        )

        request = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id',
            # Add this line to allow uploading to a Shared Drive
            supportsAllDrives=True
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logging.info(f"Uploaded {int(status.progress() * 100)}%.")
        
        logging.info(f"File '{file_name}' uploaded successfully with ID: {response.get('id')}")
        return response.get('id')