Feature: Process incoming images from LINE
  As the system, I need to correctly process webhook events from the LINE Messaging API
  so that user images can be identified and prepared for classification.

  Scenario: The system receives an image message from a known LINE user
    Given the LINE user ID "U12345abcde" is mapped to the application user "Somchai"
    And the admin has configured that user "Somchai" belongs to "Group A"
    When the system receives a LINE webhook for an image message from user "U12345abcde"
    Then the system should identify the user as "Somchai"
    And the image content should be queued for upload to "Group A"