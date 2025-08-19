from behave import *

@given('the admin has configured that user "{user}" belongs to "{group}"')
def step_impl(context, user, group):
    pass

@when('the program is executed')
def step_impl(context):
    pass

@then('a folder named "{folder_name}" should be created')
def step_impl(context, folder_name):
    pass

@then('the image from "{user}" should be saved in the "{folder_name}" folder')
def step_impl(context, user, folder_name):
    pass