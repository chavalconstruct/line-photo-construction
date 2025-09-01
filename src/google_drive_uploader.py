# src/google_drive_uploader.py

import logging
import io
import os.path
from typing import Optional, Any, List, Dict
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import shutil
import dotenv
from datetime import datetime

dotenv.load_dotenv()

class GoogleDriveService:
    """
    A wrapper class for the Google Drive API service.
    This contains the real implementation for API calls.
    """
    SCOPES: List[str] = ['https://www.googleapis.com/auth/drive']
    CREDENTIALS_FILE: str = os.getenv('CREDENTIALS_FILE_PATH', 'credentials.json')
    TOKEN_FILE: str = os.getenv('TOKEN_FILE_PATH', 'token.json')

    def __init__(self) -> None:
        """Initializes the service and handles user authentication."""
        if os.getenv('ENV') == 'production':
            writable_path: str = '/tmp/token.json'
            os.makedirs(os.path.dirname(writable_path), exist_ok=True)
            shutil.copy(self.TOKEN_FILE, writable_path)
            self.TOKEN_FILE = writable_path
            logging.info(f"Running in production. Using writable token at {self.TOKEN_FILE}")
        
        creds: Credentials = self._get_credentials()
        self.service: Any = build('drive', 'v3', credentials=creds)
        logging.info("Google Drive Service initialized successfully.")

    def _get_credentials(self) -> Credentials:
        """
        Gets valid user credentials. If not available, it initiates
        the user authentication flow.
        """
        creds: Optional[Credentials] = None
        if os.path.exists(self.TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(self.TOKEN_FILE, self.SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow: InstalledAppFlow = InstalledAppFlow.from_client_secrets_file(
                    self.CREDENTIALS_FILE, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(self.TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        return creds

    def find_or_create_folder(self, folder_name: str, parent_folder_id: Optional[str] = None) -> str:
        """
        Finds or creates a folder. If parent_folder_id is None, 
        it operates in the root of "My Drive".
        """
        query_parts: List[str] = [
            "mimeType='application/vnd.google-apps.folder'",
            f"name='{folder_name}'",
            "trashed=false"
        ]
        if parent_folder_id:
            query_parts.append(f"'{parent_folder_id}' in parents")
        
        query: str = " and ".join(query_parts)

        response: Dict[str, Any] = self.service.files().list(q=query, spaces='drive', fields='files(id)').execute()
        files: List[Dict[str, Any]] = response.get('files', [])

        if files:
            return files[0].get('id')
        else:
            file_metadata: Dict[str, Any] = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]
            
            folder: Dict[str, Any] = self.service.files().create(body=file_metadata, fields='id').execute()
            return folder.get('id')

    def upload_file(self, file_name: str, file_content: bytes, folder_id: str) -> str:
        file_metadata: Dict[str, Any] = {'name': file_name, 'parents': [folder_id]}
        media = MediaIoBaseUpload(io.BytesIO(file_content), mimetype='image/jpeg', resumable=True)
        request: Any = self.service.files().create(body=file_metadata, media_body=media, fields='id')
        
        response: Optional[Dict[str, Any]] = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logging.info(f"Uploaded {int(status.progress() * 100)}%.")
        
        logging.info(f"File '{file_name}' uploaded successfully with ID: {response.get('id')}")
        return response.get('id')
    
    def append_text_to_file(self, file_name: str, text_to_append: str, folder_id: str) -> None:
        """
        Appends a line of text to a file in Google Drive. If the file
        doesn't exist, it creates it.
        """
        query: str = f"name='{file_name}' and '{folder_id}' in parents and trashed=false"
        response: Dict[str, Any] = self.service.files().list(q=query, fields='files(id)').execute()
        files: List[Dict[str, Any]] = response.get('files', [])

        timestamp: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_text: str = f"[{timestamp}] {text_to_append}"

        if files:
            file_id: str = files[0].get('id')
            existing_content: bytes = self.service.files().get_media(fileId=file_id).execute()
            new_content: bytes = existing_content + b"\n" + formatted_text.encode('utf-8')
            
            media = MediaIoBaseUpload(io.BytesIO(new_content), mimetype='text/plain', resumable=True)
            self.service.files().update(fileId=file_id, media_body=media).execute()
            logging.info(f"Appended text to existing file '{file_name}'.")
        else:
            file_metadata: Dict[str, Any] = {'name': file_name, 'parents': [folder_id], 'mimeType': 'text/plain'}
            media = MediaIoBaseUpload(io.BytesIO(formatted_text.encode('utf-8')), mimetype='text/plain')
            self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            logging.info(f"Created new file '{file_name}' with initial text.")