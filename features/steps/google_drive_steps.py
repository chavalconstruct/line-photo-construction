from behave import *
from unittest.mock import MagicMock
from src.google_drive_uploader import upload_to_drive, GoogleDriveService

# --- Given Steps ---

@given('the user "{user}" is configured to be in "{group}"')
def step_impl(context, user, group):
    """
    Sets up the user-to-group configuration in the test context.
    """
    if not hasattr(context, 'user_configs'):
        context.user_configs = {}
    context.user_configs[user] = group

@given('the application is authorized to access Google Drive')
def step_impl(context):
    """
    Configures the mocked Google Drive service that was created
    in the before_scenario hook.
    """
    context.mock_drive_service.find_or_create_folder.return_value = 'mock_folder_id_123'
    # The 'pass' is fine, or you can remove it. The line above is the important one.
    pass
 
# --- When Steps ---

@when('the program processes an image from "{user}" named "{filename}"')
def step_impl(context, user, filename):
    """
    Simulates processing and uploading a file for a given user by calling
    the actual `upload_to_drive` function with the mocked service.
    """
    # Get the user's group from the context
    group = context.user_configs.get(user)
    
    # Call our REAL function, but pass in the MOCKED service
    upload_to_drive(
        service=context.mock_drive_service,
        file_name=filename,
        file_content=b'dummy content for behave',
        destination_folder=group
    )

# --- Then Steps ---

@then('the file "{filename}" should be uploaded to the "{folder_name}" folder on Google Drive')
def step_impl(context, filename, folder_name):
    """
    Asserts that the mocked Google Drive service was called correctly
    by the function executed in the 'when' step.
    """
    # 1. Verify that the folder creation method was called with the correct name.
    context.mock_drive_service.find_or_create_folder.assert_called_once_with(folder_name)
    
    # 2. Verify that the file upload method was called with the correct details.
    context.mock_drive_service.upload_file.assert_called_once_with(
        file_name=filename,
        file_content=b'dummy content for behave',
        folder_id='mock_folder_id_123' # This comes from our mock setup in the 'given' step
    )