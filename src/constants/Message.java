package constants;

public final class Message {

    private Message() {
    }

    public static final String MENU
            = "                     MENU\n"
            + "===============================================================\n"
            + "1. Add Student.\n" 
            + "2. Delete Student.\n"
            + "3. Search Student.\n"
            + "4. Exit.\n"
            + "===============================================================";

    public static final String INPUT_NAME = "Enter name of student: ";            
    public static final String INPUT_ID = "Enter id of student: ";            
    public static final String INPUT_CHOICE = "Enter your choice: "; 
    public static final String INPUT_SEARCH = "Enter text: "; 
    
    public static final String EMPTY_INPUT = "Input must not be empty";  
    public static final String INVALID_NUMBER = "The number input is invalid";
    public static final String POSITIVE_NUMBER = "Please input positive number";
    public static final String INVALID_RANGE = "The input range is not valid. Please enter in range %d - %d";
    public static final String INVALID_CHOICE = "Please input choice again";       
    public static final String NO_STUDENT_AVAILABLE = "The student doesn't exist in database";       
    public static final String DATABASE_EMPTY = "Database is empty";
}
