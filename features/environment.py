import os
import shutil
import json
from unittest.mock import patch, AsyncMock
from src.state_manager import StateManager
from datetime import datetime

CONFIG_TEMPLATE_PATH = "config.json.template"
CONFIG_FILE_PATH = "config.json"

def before_feature(context, feature):
    """
    Runs before each feature file to set a context name.
    """
    if "process_line_images.feature" in feature.filename:
        context.feature_name = "line_integration"
    elif "process_line_notes.feature" in feature.filename:
        context.feature_name = "note_integration" # Use a distinct name
    elif "manage_codes.feature" in feature.filename:
        context.feature_name = "management"
    else:
        context.feature_name = "classification"

def before_scenario(context, scenario):
    """
    Runs before each scenario.
    """
    # Use a short session duration for testing expiration
    context.state_manager = StateManager(session_duration_seconds=10)
    context.time_patcher = None 

    if context.feature_name == "management":
        if os.path.exists(CONFIG_TEMPLATE_PATH):
            shutil.copy(CONFIG_TEMPLATE_PATH, CONFIG_FILE_PATH)
        else:
            raise FileNotFoundError(f"Config template not found at {CONFIG_TEMPLATE_PATH}")

    elif context.feature_name == "line_integration":
        context.config_data = {"secret_code_map": {}}
        
        # --- BDD Refactoring: Mock datetime ---
        context.mocked_date = datetime(2025, 8, 30)
        context.patcher_datetime = patch('src.webhook_processor.datetime')
        MockDateTime = context.patcher_datetime.start()
        MockDateTime.now.return_value = context.mocked_date
        # ------------------------------------

        context.patcher_gdrive = patch('src.webhook_processor.GoogleDriveService')
        context.patcher_download = patch('src.webhook_processor.download_image_content', new_callable=AsyncMock)
        
        MockGoogleDriveService = context.patcher_gdrive.start()
        context.mock_gdrive_service = MockGoogleDriveService.return_value
        context.mock_download = context.patcher_download.start()
        
        # Simulate sequential return values for folder creation
        context.mock_gdrive_service.find_or_create_folder.side_effect = [
            "group_folder_id_1", "daily_folder_id_1",
            "group_folder_id_2", "daily_folder_id_2", # For subsequent calls
        ]
     
    elif context.feature_name == "note_integration":
        context.config_data = {"secret_code_map": {}}
        
        # Mock datetime
        context.mocked_date = datetime(2025, 8, 30)
        context.patcher_datetime = patch('src.webhook_processor.datetime')
        MockDateTime = context.patcher_datetime.start()
        MockDateTime.now.return_value = context.mocked_date

        # Mock GoogleDriveService
        context.patcher_gdrive = patch('src.webhook_processor.GoogleDriveService')
        MockGoogleDriveService = context.patcher_gdrive.start()
        context.mock_gdrive_service = MockGoogleDriveService.return_value
        
        # Set a return value for find_or_create_folder to be used in assertions
        context.mock_gdrive_service.find_or_create_folder.return_value = "group_folder_id_1"

    elif context.feature_name == "classification":
        if os.path.exists("Group A"): shutil.rmtree("Group A")
        if os.path.exists("Group B"): shutil.rmtree("Group B")

def after_scenario(context, scenario):
    """
    Runs after each scenario to clean up.
    """
    if hasattr(context, 'patcher_gdrive'):
        context.patcher_gdrive.stop()
        
    if hasattr(context, 'patcher_datetime'):
        context.patcher_datetime.stop()

    if hasattr(context, 'patcher_download'):
        context.patcher_download.stop()
    
    if hasattr(context, 'time_patcher') and context.time_patcher:
        context.time_patcher.stop()
