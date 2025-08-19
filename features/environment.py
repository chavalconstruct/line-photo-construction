import os
import shutil

def before_scenario(context, scenario):
    print("\n--- Cleaning up environment before scenario ---")
    if os.path.exists("Group A"):
        shutil.rmtree("Group A")
    if os.path.exists("Group B"):
        shutil.rmtree("Group B")