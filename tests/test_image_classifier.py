import pytest
from src.image_classifier import ImageClassifier

def test_get_group_folder_for_assigned_user():
    """
    Tests that the classifier can return the correct group folder
    for a user who is in the configuration.
    """
    # 1. Arrange: Prepare the inputs
    user_configs = {"Somchai": "Group A", "Somsri": "Group B"}
    file_data = {'user': 'Somchai', 'file_name': 'photo.jpg'}

    # 2. Act: Create the classifier and call the method
    classifier = ImageClassifier(user_configs)
    result_folder = classifier.get_group_folder(file_data)

    # 3. Assert: Check if the output is correct
    assert result_folder == "Group A"

def test_get_group_folder_for_unassigned_user():
    """
    Tests that the classifier returns None for a user who is not in the config.
    """
    # 1. Arrange
    user_configs = {"Somchai": "Group A"} # Note: 'Somsri' is not in this config
    file_data = {'user': 'Somsri', 'file_name': 'somsri_photo.jpg'}

    # 2. Act
    classifier = ImageClassifier(user_configs)
    result_folder = classifier.get_group_folder(file_data)

    # 3. Assert
    assert result_folder is None