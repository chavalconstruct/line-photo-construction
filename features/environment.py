# features/environment.py
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
        context.feature_name = "note_integration"
    elif "manage_codes.feature" in feature.filename:
        context.feature_name = "management"
    else:
        context.feature_name = "classification"

def before_scenario(context, scenario):
    """
    Runs before each scenario.
    """
    context.state_manager = StateManager(session_duration_seconds=10)
    context.time_patcher = None 

    if context.feature_name == "management":
        if os.path.exists(CONFIG_TEMPLATE_PATH):
            shutil.copy(CONFIG_TEMPLATE_PATH, CONFIG_FILE_PATH)
        else:
            raise FileNotFoundError(f"Config template not found at {CONFIG_TEMPLATE_PATH}")

    elif context.feature_name == "line_integration":
        context.config_data = {"secret_code_map": {}}
        
        context.mocked_date = datetime(2025, 8, 30)
        
        # --- FIX: Patch 'datetime' where it's used (in the handler) ---
        context.patcher_datetime = patch('src.handlers.image_message_handler.datetime')
        MockDateTime = context.patcher_datetime.start()
        MockDateTime.now.return_value = context.mocked_date

        # --- FIX: Patch 'GoogleDriveService' where it's used ---
        context.patcher_gdrive = patch('src.handlers.image_message_handler.GoogleDriveService')
        
        # --- FIX: Patch 'download_image_content' where it's defined ---
        context.patcher_download = patch('src.handlers.image_message_handler.download_image_content', new_callable=AsyncMock)
        
        MockGoogleDriveService = context.patcher_gdrive.start()
        context.mock_gdrive_service = MockGoogleDriveService.return_value
        context.mock_download = context.patcher_download.start()
        
        context.mock_gdrive_service.find_or_create_folder.side_effect = [
            "group_folder_id_1", "daily_folder_id_1",
            "group_folder_id_2", "daily_folder_id_2",
        ]
     
    elif context.feature_name == "note_integration":
        context.config_data = {"secret_code_map": {}}
        
        context.mocked_date = datetime(2025, 8, 30)
        
        # --- FIX: Patch 'datetime' where it's used (in the handler) ---
        context.patcher_datetime = patch('src.handlers.text_message_handler.datetime')
        MockDateTime = context.patcher_datetime.start()
        MockDateTime.now.return_value = context.mocked_date

        # --- FIX: Patch 'GoogleDriveService' where it's used ---
        context.patcher_gdrive = patch('src.handlers.text_message_handler.GoogleDriveService')
        MockGoogleDriveService = context.patcher_gdrive.start()
        context.mock_gdrive_service = MockGoogleDriveService.return_value
        
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