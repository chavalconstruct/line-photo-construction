Feature: Manage secret codes via chat commands as an admin

  Scenario: An admin successfully adds a new secret code
    Given the system is configured with "U123_Admin" as an admin user
    When admin user "U123_Admin" sends the message "add code #s3 for group Group_C_New"
    Then the bot should reply with "Success: Code #s3 has been added for group Group_C_New."
    And the secret code "#s3" should now be mapped to the group "Group_C_New"

  Scenario: An admin successfully removes an existing secret code
    Given the system is configured with "U123_Admin" as an admin user
    When admin user "U123_Admin" sends the message "remove code #s2"
    Then the bot should reply with "Success: Code #s2 has been removed."
    And the secret code "#s2" should no longer exist in the configuration

  Scenario: A non-admin user tries to use an admin command
    Given the system is configured with "U456_NormalUser" as a non-admin user
    When non-admin user "U456_NormalUser" sends the message "remove code #s1"
    Then the bot should reply with "Error: You do not have permission to use this command."
    And the secret code "#s1" should still be mapped to the group "Group_A_Photos"

  Scenario: An admin tries to remove a non-existent secret code
    Given the system is configured with "U123_Admin" as an admin user
    When admin user "U123_Admin" sends the message "remove code #code_that_does_not_exist"
    Then the bot should reply with "Error: Code #code_that_does_not_exist was not found and could not be removed."