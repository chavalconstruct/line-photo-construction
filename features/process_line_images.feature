Feature: Process images from a LINE webhook using a dynamic user session workflow

  Scenario: A user sends an image without a preceding secret code
    When user "U123" sends an image
    Then no files should be uploaded

  Scenario: A user successfully starts a session and uploads a single image
    Given the secret code "#s1" is configured for the "Group_A_Photos" folder
    When user "U123" sends a text message with "#s1"
    And user "U123" sends an image
    Then the image from user "U123" should be uploaded to the "Group_A_Photos" folder

  Scenario: Another user interrupts the workflow and fails to upload
    Given the secret code "#s1" is configured for the "Group_A_Photos" folder
    When user "U123" sends a text message with "#s1"
    And another user "U456" sends an image
    Then the interrupting image from "U456" was not uploaded
    When user "U123" sends another image
    Then the image from user "U123" should be uploaded to the "Group_A_Photos" folder

  Scenario: A user successfully uploads multiple images within a session
    Given the secret code "#s1" is configured for the "Group_A_Photos" folder
    When user "U123" sends a text message with "#s1"
    And user "U123" sends an image
    Then the image from user "U123" should be uploaded to the "Group_A_Photos" folder
    When user "U123" sends another image
    Then the second image from user "U123" should also be uploaded to the "Group_A_Photos" folder

  Scenario: An image upload fails after the session has expired
    Given the secret code "#s1" is configured for the "Group_A_Photos" folder
    When user "U123" sends a text message with "#s1"
    And the session for user "U123" expires
    When user "U123" sends an image
    Then no files should be uploaded