from src.google_drive_uploader import GoogleDriveService

print("Attempting to authenticate to generate token.json...")
print("Your web browser will open for you to log in.")

# Just creating an instance of the class will trigger the login flow
try:
    service = GoogleDriveService()
    print("\nSUCCESS: token.json has been created successfully.")
except Exception as e:
    print(f"\nERROR: An error occurred: {e}")