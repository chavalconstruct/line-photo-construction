Feature: Classify images by user group

  Scenario: A user from a defined group sends an image
    Given the admin has configured that user "Somchai" belongs to "Group A"
    When the program is executed
    Then a folder named "Group A" should be created
    And the image from "Somchai" should be saved in the "Group A" folder

  Scenario: Multiple users from different groups send images
    Given the admin has configured that user "Somchai" belongs to "Group A"
    And the admin has configured that user "Somsri" belongs to "Group B"
    When the program is executed with multiple images
    Then a folder named "Group A" should be created
    And the image from "Somchai" should be saved in the "Group A" folder
    And a folder named "Group B" should be created
    And the image from "Somsri" should be saved in the "Group B" folder

  Scenario: A user not in any group sends an image
    Given the admin has configured that user "Somchai" belongs to "Group A"
    When the program is executed with an image from unassigned user "Somsri"
    Then no new folders should be created
    And a warning for user "Somsri" should be logged
  
Scenario Outline: The system correctly counts saved images based on input
  Given the admin has configured that user "Somchai" belongs to "Group A"
  And the admin has configured that user "Somsak" belongs to "Group A"
  When <test_case>
  Then the "Group A" folder should contain <expected_count> image(s)

  Examples:
    | test_case                                                      | expected_count |
    | the program is executed with images from the same group        | 2              |
    | the program is executed with only a non-image file             | 0              |
    | the program is executed with a mixed batch of files from "Somchai" | 1              |