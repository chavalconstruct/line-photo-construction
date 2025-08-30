Feature: Process and save text notes from a LINE webhook

  Scenario: A user successfully starts a session and saves multiple notes
    Given the secret code "#s1" is configured for the "Group_A_Notes" folder
    When user "U123" sends a text message with "#s1 This is the first note"
    And user "U123" sends another text message with "This is the second note"
    Then the note "This is the first note" should be saved to the "Group_A_Notes" folder
    And the note "This is the second note" should also be saved to the "Group_A_Notes" folder

  Scenario: A user sends a note after their session has expired
    Given the secret code "#s1" is configured for the "Group_A_Notes" folder
    When user "U123" sends a text message with "#s1"
    And the session for user "U123" expires
    And user "U123" sends another text message with "This note should not be saved"
    Then no notes should be saved