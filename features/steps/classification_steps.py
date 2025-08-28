from behave import *
import os
from src.image_classifier import classify_and_save_image

@given('the admin has configured that user "{user}" belongs to "{group}"')
def step_impl(context, user, group):
    if not hasattr(context, 'user_configs'):
        context.user_configs = {}
    context.user_configs[user] = group

# --- When Steps ---
def process_files(context):
    """Helper function to process files stored in context."""
    if not hasattr(context, 'warnings'):
        context.warnings = []

    for file_data in context.files_to_process:
        # We only process images for now
        if file_data.get('type') == 'image':
            was_saved = classify_and_save_image(context.user_configs, file_data)
            if not was_saved:
                warning = f"Warning: User '{file_data['user']}' is not assigned to any group."
                context.warnings.append(warning)

@when('the program is executed')
def step_impl(context):
    context.files_to_process = [
        {'user': 'Somchai', 'file_name': 'somchai_photo_01.jpg', 'content': b'd', 'type': 'image'}
    ]
    process_files(context)

@when('the program is executed with multiple images')
def step_impl(context):
    context.files_to_process = [
        {'user': 'Somchai', 'file_name': 'somchai_photo_02.jpg', 'content': b'd', 'type': 'image'},
        {'user': 'Somsri', 'file_name': 'somsri_selfie_01.png', 'content': b'd', 'type': 'image'}
    ]
    process_files(context)

@when('the program is executed with an image from unassigned user "{user}"')
def step_impl(context, user):
    context.files_to_process = [
        {'user': user, 'file_name': 'unknown.jpg', 'content': b'd', 'type': 'image'}
    ]
    process_files(context)

@when('the program is executed with images from the same group')
def step_impl(context):
    context.files_to_process = [
        {'user': 'Somchai', 'file_name': 'somchai_photo_03.jpg', 'content': b'd', 'type': 'image'},
        {'user': 'Somsak', 'file_name': 'somsak_work_01.jpg', 'content': b'd', 'type': 'image'}
    ]
    process_files(context)

@when('the program is executed with only a non-image file')
def step_impl(context):
    context.files_to_process = [
        {'user': 'Somchai', 'file_name': 'meeting_notes.docx', 'content': b'd', 'type': 'document'}
    ]
    process_files(context)

@when('the program is executed with a mixed batch of files from "{user}"')
def step_impl(context, user):
    context.files_to_process = [
        {'user': user, 'file_name': 'annual_report.pdf', 'content': b'd', 'type': 'document'},
        {'user': user, 'file_name': 'vacation_photo.jpg', 'content': b'd', 'type': 'image'}
    ]
    process_files(context)

# --- Then Steps ---

@then('a folder named "{folder_name}" should be created')
def step_impl(context, folder_name):
    assert os.path.isdir(folder_name), f"Folder '{folder_name}' was not found."

@then('the image from "{user}" should be saved in the "{folder_name}" folder')
def step_impl(context, user, folder_name):
    # This step now only VERIFIES existence, it doesn't create the file.
    file_info = next((f for f in context.files_to_process if f['user'] == user and f['type'] == 'image'), None)
    assert file_info is not None, f"No image file found in context for user {user}."

    expected_path = os.path.join(folder_name, file_info['file_name'])
    assert os.path.exists(expected_path), f"File '{expected_path}' was not found."

@then('the "{folder_name}" folder should contain {count:d} image(s)')
def step_impl(context, folder_name, count):
    if not os.path.exists(folder_name):
        file_count = 0
    else:
        # Count only files, not subdirectories
        file_count = len([name for name in os.listdir(folder_name) if os.path.isfile(os.path.join(folder_name, name))])
    assert file_count == count, f"Expected {count} file(s) in '{folder_name}', but found {file_count}."

@then('no new folders should be created')
def step_impl(context):
    # We check if specific group folders exist.
    assert not os.path.exists("Group A")
    assert not os.path.exists("Group B")
    # A more robust check could be added if needed.

@then('a warning for user "{user}" should be logged')
def step_impl(context, user):
    expected_warning = f"Warning: User '{user}' is not assigned to any group."
    assert expected_warning in context.warnings, f"Expected warning for user '{user}' was not logged."







