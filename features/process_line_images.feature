Feature: Process images from a LINE webhook and upload to Google Drive

  Scenario: A known user sends an image
    Given a mapping of LINE user IDs to application users
      """
      { "U12345": "Alice" }
      """
    And user configurations for Google Drive folders
      """
      { "Alice": "Group_A_Photos" }
      """
    When the system receives a LINE webhook for an image message from user "U12345"
    Then the image from "Alice" should be uploaded to her assigned group folder