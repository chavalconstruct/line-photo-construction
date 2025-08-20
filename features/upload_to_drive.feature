Feature: Upload classified images to Google Drive
  As an admin, I want classified images to be automatically uploaded to the correct
  Google Drive folder so that they are securely backed up and organized.

  Scenario: A classified image is uploaded to the correct folder on Google Drive
    Given the user "Somchai" is configured to be in "Group A"
    And the application is authorized to access Google Drive
    When the program processes an image from "Somchai" named "somchai_image.jpg"
    Then the file "somchai_image.jpg" should be uploaded to the "Group A" folder on Google Drive