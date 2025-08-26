import os
import shutil
from unittest.mock import patch, AsyncMock
from src.state_manager import StateManager

def before_feature(context, feature):
    """
    Runs before each feature file. We use this to decide which
    setup is needed for the scenarios within that feature.
    """
    # We now set a flag based on the feature file name
    if "process_line_images.feature" in feature.filename:
        context.feature_name = "line_integration"
    elif "manage_codes.feature" in feature.filename:
        context.feature_name = "management"
    else:
        context.feature_name = "classification"

def before_scenario(context, scenario):
    """
    Runs before each scenario.
    """
    # ALWAYS create a state manager, as it's needed by multiple features
    context.state_manager = StateManager()

    if context.feature_name == "line_integration":
        # --- SETUP FOR LINE INTEGRATION TESTS (using mocks) ---
        context.patcher_gdrive = patch('src.webhook_processor.GoogleDriveService')
        context.patcher_download = patch('src.webhook_processor.download_image_content', new_callable=AsyncMock)

        MockGoogleDriveService = context.patcher_gdrive.start()
        context.mock_gdrive_service = MockGoogleDriveService.return_value
        context.mock_download = context.patcher_download.start()
    
    elif context.feature_name == "classification":
        # --- SETUP FOR CLASSIFICATION TESTS (real file system) ---
        print("\n--- Cleaning up local folders for classification test ---")
        if os.path.exists("Group A"):
            shutil.rmtree("Group A")
        if os.path.exists("Group B"):
            shutil.rmtree("Group B")
    
    # NOTE: The 'management' feature only needs the state_manager,
    # which is already created above. No extra setup needed.


def after_scenario(context, scenario):
    """
    Runs after each scenario to clean up.
    """
    if context.feature_name == "line_integration":
        # Stop the patchers only if they were started
        context.patcher_gdrive.stop()
        context.patcher_download.stop()