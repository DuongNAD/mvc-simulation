package view;

import dto.StudentResponseDTO;
import java.util.List;

public class StudentView {

    public StudentView() {
    }

    public void displayStudents(List<StudentResponseDTO> students) {
        if (students == null || students.isEmpty()) {
            System.out.println("No students found.");
            return;
        }
        System.out.println("---------------------------------------------------------------");
        System.out.printf("%-10s%-25s%-25s\n", "ID", "Name", "Created At");
        System.out.println("---------------------------------------------------------------");
        for (StudentResponseDTO student : students) {
            System.out.println(student.getDisplayString());
        }
        System.out.println("---------------------------------------------------------------");
    }

    public void displayMessage(String message) {
        System.out.println(message);
    }
}
