package dto;

public class StudentResponseDTO {
    private int id;
    private String message;
    private String displayString;

    public StudentResponseDTO() {
    }

    public StudentResponseDTO(int id, String message, String displayString) {
        this.id = id;
        this.message = message;
        this.displayString = displayString;
    }

    public int getId() {
        return id;
    }

    public void setId(int id) {
        this.id = id;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public String getDisplayString() {
        return displayString;
    }

    public void setDisplayString(String displayString) {
        this.displayString = displayString;
    }

    @Override
    public String toString() {
        return displayString;
    }
}
