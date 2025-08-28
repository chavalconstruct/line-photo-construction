import os

class ImageClassifier:
    """
    Handles the logic for classifying images based on user configurations.
    """
    def __init__(self, user_configs):
        """
        Initializes the classifier with user-to-group mappings.
        
        Args:
            user_configs (dict): A dictionary mapping user names to group folder names.
        """
        self._user_configs = user_configs

    def get_group_folder(self, file_data):
        """
        Determines the group folder for a given file based on the user.
        
        Args:
            file_data (dict): A dictionary containing file metadata, including 'user'.
            
        Returns:
            str: The name of the group folder, or None if the user is not found.
        """
        user = file_data.get('user')
        return self._user_configs.get(user)

def classify_and_save_image(user_configs, image_data):
    """
    Uses the classifier to decide the group and then saves the image file.

    Args:
        user_configs (dict): A dictionary mapping users to their groups.
        image_data (dict): A dictionary containing image details like 'user', 
                           'file_name', and 'content'.
    
    Returns:
        bool: True if the file was saved successfully, False otherwise.
    """
    # 1. Use the classifier to make a decision
    classifier = ImageClassifier(user_configs)
    group = classifier.get_group_folder(image_data)

    # 2. Perform the action based on the decision
    if group:
        if not os.path.exists(group):
            os.makedirs(group)
        
        file_path = os.path.join(group, image_data['file_name'])
        with open(file_path, 'wb') as f:
            f.write(image_data.get('content', b''))
        
        return True
    
    return False