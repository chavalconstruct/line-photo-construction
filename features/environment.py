import os
import shutil
from unittest.mock import patch, AsyncMock
from src.state_manager import StateManager

def before_feature(context, feature):
    """
    Runs before each feature file. We use this to decide which
    setup is needed for the scenarios within that feature.
    """
    if "process_line_images.feature" in feature.filename:
        # This flag tells before_scenario to use mocks
        context.use_mocks = True
    else:
        context.use_mocks = False

def before_scenario(context, scenario):
    """
    Runs before each scenario.
    """
    if context.use_mocks:
        # --- SETUP FOR LINE INTEGRATION TESTS (using mocks) ---
        context.state_manager = StateManager()
        context.patcher_gdrive = patch('src.webhook_processor.GoogleDriveService')
        context.patcher_download = patch('src.webhook_processor.download_image_content', new_callable=AsyncMock)

        MockGoogleDriveService = context.patcher_gdrive.start()
        context.mock_gdrive_service = MockGoogleDriveService.return_value
        context.mock_download = context.patcher_download.start()
    else:
        # --- SETUP FOR CLASSIFICATION TESTS (real file system) ---
        print("\n--- Cleaning up local folders for classification test ---")
        if os.path.exists("Group A"):
            shutil.rmtree("Group A")
        if os.path.exists("Group B"):
            shutil.rmtree("Group B")

def after_scenario(context, scenario):
    """
    Runs after each scenario to clean up.
    """
    if context.use_mocks:
        # Stop the patchers only if they were started
        context.patcher_gdrive.stop()
        context.patcher_download.stop()