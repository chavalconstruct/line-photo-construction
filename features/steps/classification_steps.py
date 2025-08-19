from behave import *
import os


@given('the admin has configured that user "{user}" belongs to "{group}"')
def step_impl(context, user, group):
    if not hasattr(context, 'user_configs'):
        context.user_configs = {}
    context.user_configs[user] = group

@when('the program is executed with multiple images')
def step_impl(context):
    context.new_images = [
        {'user': 'Somchai', 'image_name': 'somchai_photo_02.jpg'},
        {'user': 'Somsri', 'image_name': 'somsri_selfie_01.png'}
    ]

@when('the program is executed')
def step_impl(context):
    context.new_images = [
        {'user': 'Somchai', 'image_name': 'somchai_photo_01.jpg'}
    ]

@when('the program is executed with images from the same group')
def step_impl(context):
    context.new_files = [
        {'user': 'Somchai', 'file_name': 'somchai_photo_03.jpg', 'type': 'image'},
        {'user': 'Somsak', 'file_name': 'somsak_work_01.jpg', 'type': 'image'}
    ]
    
    images_to_process = [f for f in context.new_files if f.get('type') == 'image']
    for image in images_to_process:
        process_image(context, image)

@when('the program is executed with an image from unassigned user "{user}"')
def step_impl(context, user):
    context.new_images = [
        {'user': user, 'image_name': 'somsri_unknown_pic.jpg'}
    ]
    context.processed_folders = []
    context.warnings = []

    for image in context.new_images:
        current_user = image['user']
        group = context.user_configs.get(current_user) 

        if group:
            folder_name = group
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
            context.processed_folders.append(folder_name)
        else:
            warning_message = f"Warning: User '{current_user}' is not assigned to any group."
            context.warnings.append(warning_message)
            print(warning_message) 

@when('the program is executed with only a non-image file')
def step_impl(context):
    context.new_files = [
        {'user': 'Somchai', 'file_name': 'meeting_notes.docx', 'type': 'document'}
    ]
    
    images_to_process = [f for f in context.new_files if f.get('type') == 'image']
    for image in images_to_process:
        process_image(context, image)

@when('the program is executed with a mixed batch of files from "{user}"')
def step_impl(context, user):
    
    context.new_files = [
        {'user': user, 'file_name': 'annual_report.pdf', 'type': 'document'},
        {'user': user, 'file_name': 'vacation_photo.jpg', 'type': 'image'}
    ]
    
    images_to_process = [f for f in context.new_files if f.get('type') == 'image']
    for image in images_to_process:
        process_image(context, image)

@then('the "{folder_name}" folder should contain {count:d} image(s)')
def step_impl(context, folder_name, count):
    if not os.path.exists(folder_name):
        file_count = 0
    else:
        file_count = len(os.listdir(folder_name))
    
    assert file_count == count, f"Expected {count} file(s), but found {file_count}."

@then('no new folders should be created')
def step_impl(context):
    assert len(context.processed_folders) == 0, f"Expected 0 folders, but {len(context.processed_folders)} were created."

@then('a warning for user "{user}" should be logged')
def step_impl(context, user):
    expected_warning = f"Warning: User '{user}' is not assigned to any group."
    assert expected_warning in context.warnings, f"Expected warning for user '{user}' was not logged."

@then('a folder named "{folder_name}" should be created')
def step_impl(context, folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    assert os.path.isdir(folder_name), f"Folder '{folder_name}' was not found."

@then('the image from "{user}" should be saved in the "{folder_name}" folder')
def step_impl(context, user, folder_name):
    image_to_save = next((img for img in context.new_images if img['user'] == user), None)
    assert image_to_save is not None, f"No image found for user {user}"

    file_path = os.path.join(folder_name, image_to_save['image_name'])
    with open(file_path, 'w') as f:
        f.write("This is a dummy image file.")
    assert os.path.exists(file_path), f"Image file '{file_path}' was not found."


def process_image(context, image_data):
    """A helper function to process and save a single image."""
    user = image_data['user']
    group = context.user_configs.get(user)
    if group:
        if not os.path.exists(group):
            os.makedirs(group)
        file_path = os.path.join(group, image_data['file_name'])
        with open(file_path, 'w') as f:
            f.write("dummy image content")    