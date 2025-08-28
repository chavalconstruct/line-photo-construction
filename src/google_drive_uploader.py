"""
This module handles the interaction with the Google Drive API for uploading files.
"""
import logging
import io
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import shutil
import dotenv

dotenv.load_dotenv()


class GoogleDriveService:
    """
    A wrapper class for the Google Drive API service.
    This contains the real implementation for API calls.
    """
    SCOPES = ['https://www.googleapis.com/auth/drive']
    CREDENTIALS_FILE = os.getenv('CREDENTIALS_FILE_PATH', 'credentials.json')
    TOKEN_FILE = os.getenv('TOKEN_FILE_PATH', 'token.json')

    def __init__(self):
        """Initializes the service and handles user authentication."""
        # If running in production, copy the read-only token to a writable location
        if os.getenv('ENV') == 'production':
            writable_path = '/tmp/token.json'
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(writable_path), exist_ok=True)
            # Copy the secret file to the writable path
            shutil.copy(self.TOKEN_FILE, writable_path)
            # Point TOKEN_FILE to the new writable path
            self.TOKEN_FILE = writable_path
            logging.info(f"Running in production. Using writable token at {self.TOKEN_FILE}")
        creds = self._get_credentials()
        self.service = build('drive', 'v3', credentials=creds)
        logging.info("Google Drive Service initialized successfully.")

    def _get_credentials(self):
        """
        Gets valid user credentials. If not available, it initiates
        the user authentication flow.
        """
        creds = None
        if os.path.exists(self.TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(self.TOKEN_FILE, self.SCOPES)
        
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.CREDENTIALS_FILE, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(self.TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        return creds

    def find_or_create_folder(self, folder_name, parent_folder_id=None):
        """
        Finds or creates a folder. If parent_folder_id is None, 
        it operates in the root of "My Drive".
        """
        # Build the search query
        query_parts = [
            "mimeType='application/vnd.google-apps.folder'",
            f"name='{folder_name}'",
            "trashed=false"
        ]
        if parent_folder_id:
            query_parts.append(f"'{parent_folder_id}' in parents")
        
        query = " and ".join(query_parts)

        response = self.service.files().list(q=query, spaces='drive', fields='files(id)').execute()
        files = response.get('files', [])

        if files:
            return files[0].get('id')
        else:
            file_metadata = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]
            
            folder = self.service.files().create(body=file_metadata, fields='id').execute()
            return folder.get('id')

    def upload_file(self, file_name, file_content, folder_id):
        # This method's logic remains the same
        file_metadata = {'name': file_name, 'parents': [folder_id]}
        media = MediaIoBaseUpload(io.BytesIO(file_content), mimetype='image/jpeg', resumable=True)
        request = self.service.files().create(body=file_metadata, media_body=media, fields='id')
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logging.info(f"Uploaded {int(status.progress() * 100)}%.")
        
        logging.info(f"File '{file_name}' uploaded successfully with ID: {response.get('id')}")
        return response.get('id')
