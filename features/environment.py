import os
import shutil
from unittest.mock import patch

def before_scenario(context, scenario):
    """
    This runs before each scenario.
    We'll set up mocks here.
    """
    print("\n--- Cleaning up environment before scenario ---")
    if os.path.exists("Group A"):
        shutil.rmtree("Group A")
    if os.path.exists("Group B"):
        shutil.rmtree("Group B")

    # Start the patcher for GoogleDriveService
    # This replaces the real class with a mock for the duration of the scenario
    context.patcher = patch('src.google_drive_uploader.GoogleDriveService')
    MockGoogleDriveService = context.patcher.start()

    # Create an instance of the mock and attach it to the context
    # This is what our steps will interact with
    context.mock_drive_service = MockGoogleDriveService.return_value

def after_scenario(context, scenario):
    """
    This runs after each scenario.
    We'll stop the patcher here to clean up.
    """
    # Stop the patcher, restoring the original class
    context.patcher.stop()