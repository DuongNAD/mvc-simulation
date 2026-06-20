/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package constants;

public final class Message {

    //private Contructor
    private Message(){
    }
    
    //message menu
    public static final String MENU
            = "                     MENU\n"
            + "===============================================================\n"
            + "1. Add Doctor.\n" 
            + "2. Update Doctor.\n"
            + "3. Delete Doctor.\n"
            + "4. Search Doctor.\n"
            + "5. Exit.\n"
            + "===============================================================";

    //thong bao nhap
    public static final String INPUT_CODE = "Enter code of doctor: ";            
    public static final String INPUT_NAME = "Enter name of doctor: ";            
    public static final String INPUT_SPECIALIZATION = "Enter Specialization: ";            
    public static final String INPUT_AVAILABILITY = "Enter Availability: ";            
    public static final String INPUT_CHOICE = "Enter your choice: "; 
    public static final String INPUT_SEARCH = "Enter text: "; 
    
    //thong bao loi
    public static final String EMPTY_INPUT = "Input must not be empty";  
    public static final String INVALID_NUMBER = "The number input is invalid";
    public static final String DUPLICATE = "The doctor code has already exist in database.";
    public static final String POSITIVE_NUMBER = "Please input positive number";
    public static final String INVALID_RANGE = "The input range is not valid. Please enter in range %d - %d";
    public static final String INVALID_CHOICE = "Please input choice again";       
    public static final String NO_DOCTOR_AVAILABLE = "The doctor doesn't exist in database";       
    public static String DATABASE_EMPTY = "Database is empty";
}
