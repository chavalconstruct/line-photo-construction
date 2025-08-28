Feature: Process images from a LINE webhook using a stateful secret code workflow

  Scenario: A user sends a secret code and then an image successfully
    Given the secret code "#s1" is configured for the "Group_A_Photos" folder
    And the system is ready to process events for user "Alice" with LINE ID "U12345"
    When user "Alice" sends a text message with "#s1"
    And user "Alice" sends an image
    Then the image from "Alice" should be uploaded to the "Group_A_Photos" folder

  Scenario: Another user interrupts the workflow
    Given the secret code "#s1" is configured for the "Group_A_Photos" folder
    And the system is ready to process events for user "Alice" with LINE ID "U12345"
    And the system is ready to process events for user "Bob" with LINE ID "U67890"
    When user "Alice" sends a text message with "#s1"
    And user "Bob" sends an image
    Then no files should be uploaded
    When user "Alice" sends an image
    Then the image from "Alice" should be uploaded to the "Group_A_Photos" folder

  Scenario: A user sends an image without a preceding secret code
    Given the system is ready to process events for user "Alice" with LINE ID "U12345"
    When user "Alice" sends an image
    Then no files should be uploaded

  Scenario: A user successfully uploads multiple images within a session
    Given the secret code "#s1" is configured for the "Group_A_Photos" folder
    And the system is ready to process events for user "Alice" with LINE ID "U12345"
    When user "Alice" sends a text message with "#s1"
    And user "Alice" sends an image
    Then the image from "Alice" should be uploaded to the "Group_A_Photos" folder
    When user "Alice" sends another image
    Then the second image from "Alice" should also be uploaded to the "Group_A_Photos" folder

  Scenario: An image upload fails after the session has expired
    Given the secret code "#s1" is configured for the "Group_A_Photos" folder
    And the system is ready to process events for user "Alice" with LINE ID "U12345"
    When user "Alice" sends a text message with "#s1"
    And the session for user "Alice" expires
    When user "Alice" sends an image
    Then no files should be uploaded