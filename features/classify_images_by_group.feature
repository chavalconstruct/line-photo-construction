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
  
  Scenario: Multiple users from the same group send images
    Given the admin has configured that user "Somchai" belongs to "Group A"
    And the admin has configured that user "Somsak" belongs to "Group A"
    When the program is executed with images from the same group
    Then the folder "Group A" should contain 2 images

  Scenario: A user not in any group sends an image
    Given the admin has configured that user "Somchai" belongs to "Group A"
    When the program is executed with an image from unassigned user "Somsri"
    Then no new folders should be created
    And a warning for user "Somsri" should be logged
  
  Scenario: A user sends a non-image file
    Given the admin has configured that user "Somchai" belongs to "Group A"
    When the program is executed with a non-image file from "Somchai"
    Then the "Group A" folder should contain 0 images