Feature: Test 123
   Scenario: counting
      Given I have the desktop running
      When I reopen the app store 100 times
      Then the memory should not be higher than 850MB
