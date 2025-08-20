import os
import shutil
from src.image_classifier import classify_and_save_image

def test_save_image_for_known_user_creates_folder_and_file():
    """
    Tests that a folder and file are created for a user with a defined group.
    """
    # 1. Setup: Prepare data and environment for the test.
    user_configs = {"Somchai": "Group A"}
    image_data = {
        'user': 'Somchai',
        'file_name': 'somchai_photo_01.jpg',
        'content': b'This is a dummy image content.'
    }
    group_folder = user_configs['Somchai']

    # Clean up old directory (if any) to ensure a clean test environment.
    if os.path.exists(group_folder):
        shutil.rmtree(group_folder)

    # 2. Action: Call the function under test.
    classify_and_save_image(user_configs, image_data)

    # 3. Assert: Verify that the outcome matches the expectation.
    expected_file_path = os.path.join(group_folder, image_data['file_name'])

    assert os.path.isdir(group_folder), f"Folder '{group_folder}' should have been created."
    assert os.path.exists(expected_file_path), f"File '{expected_file_path}' should exist."

    # 4. Teardown: Remove created files/folders to not affect other tests.
    shutil.rmtree(group_folder)