package utils;

import constants.Message;

public final class Validation {

    private Validation() {
    }

    public static String getString(String input) throws Exception {
        if (input == null || input.trim().isEmpty()) {
            throw new Exception(Message.EMPTY_INPUT);
        }
        return input.trim();
    }
    
    public static int getPosititveInteger(String input) throws Exception {
        try {
            int number = Integer.parseInt(input.trim());
            if (number <= 0) {
                throw new Exception(Message.POSITIVE_NUMBER);
            }
            return number;
        } catch (NumberFormatException e) {
            throw new Exception(Message.INVALID_NUMBER);
        }
    }
    
    public static int getChoice(String input, int min, int max) throws Exception {
        try {
            int choice = Integer.parseInt(input.trim());
            if (choice < min || choice > max) {
                throw new Exception(String.format(Message.INVALID_RANGE, min, max));
            }
            return choice;
        } catch (Exception e) {
            throw new Exception(Message.INVALID_NUMBER);
        }
    }
}
