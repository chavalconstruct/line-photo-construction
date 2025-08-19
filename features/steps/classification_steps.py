from behave import *
import os

@given('the admin has configured that user "{user}" belongs to "{group}"')
def step_impl(context, user, group):
    if not hasattr(context, 'user_configs'):
        context.user_configs = {}
    context.user_configs[user] = group

@when('the program is executed')
def step_impl(context):
    context.new_images = [
        {'user': 'Somchai', 'image_name': 'somchai_photo_01.jpg'}
    ]

@then('a folder named "{folder_name}" should be created')
def step_impl(context, folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    assert os.path.isdir(folder_name), f"Folder '{folder_name}' was not found."

@then('the image from "{user}" should be saved in the "{folder_name}" folder')
def step_impl(context, user, folder_name):
    image_to_save = context.new_images[0]
    file_path = os.path.join(folder_name, image_to_save['image_name'])
    with open(file_path, 'w') as f:
        f.write("This is a dummy image file.")
    assert os.path.exists(file_path), f"Image file '{file_path}' was not found."