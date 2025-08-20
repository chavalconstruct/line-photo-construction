import os

def classify_and_save_image(user_configs, image_data):
    """
    Classifies and saves an image based on the user's group.

    Args:
        user_configs (dict): A dictionary mapping users to their groups.
        image_data (dict): A dictionary containing image details like
                           'user', 'file_name', and 'content'.
    """
    user = image_data.get('user')
    group = user_configs.get(user)

    if group:
        # Create the group folder if it doesn't exist.
        if not os.path.exists(group):
            os.makedirs(group)

        # Save the image file.
        file_path = os.path.join(group, image_data['file_name'])
        with open(file_path, 'wb') as f:
            f.write(image_data.get('content', b''))