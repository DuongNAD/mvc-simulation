/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package utils;

import constants.Message;

public final class Validation {

    //contructor
    private Validation() {
    }

    //ham nhap chuoi va validate
    public static String getString(String input) throws Exception {
        if (input == null || input.isEmpty()) {
            throw new Exception(Message.EMPTY_INPUT);
        }
        return input.trim();
    }
    
    //Ham lay so nguyen duong 
    public static int getPosititveInteger(String input) throws Exception{
        try {
            int number = Integer.parseInt(input);
            //kiem tra xem so co > 0 hay k
            if(number <= 0){
                throw new Exception(Message.POSITIVE_NUMBER);
            }
            return number;
        } catch (NumberFormatException e) {
            //thong bao loi
            throw new Exception(Message.INVALID_NUMBER);
        }
    }
    
    //Ham validate choice
    public static int getChoice(String input, int min, int max) throws Exception{
        try {
            int choice = Integer.parseInt(input);
            if((choice < min) || (choice > max)){
                throw new Exception(String.format(Message.INVALID_RANGE, min, max));
            }
            return choice;
        } catch (Exception e) {
            //thong bao loi
            throw new Exception(Message.INVALID_NUMBER);
        }
    }
}
