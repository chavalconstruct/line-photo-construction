Feature: Classify images by user group

  Scenario: A user from a defined group sends an image
    Given the admin has configured that user "Somchai" belongs to "Group A"
    When the program is executed
    Then a folder named "Group A" should be created
    And the image from "Somchai" should be saved in the "Group A" folder