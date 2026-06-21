package controller;

import dto.StudentRequestDTO;
import dto.StudentResponseDTO;
import service.StudentService;
import view.StudentView;
import java.util.List;

public class StudentController {
    private final StudentService studentService;
    private final StudentView studentView;

    public StudentController(StudentService studentService, StudentView studentView) {
        this.studentService = studentService;
        this.studentView = studentView;
    }

    public void addStudent(StudentRequestDTO requestDTO) {
        try {
            StudentResponseDTO response = studentService.addStudent(requestDTO);
            studentView.displayMessage(response.getMessage());
        } catch (Exception e) {
            studentView.displayMessage(e.getMessage());
        }
    }

    public void deleteStudent(int id) {
        try {
            StudentResponseDTO response = studentService.deleteStudent(id);
            studentView.displayMessage(response.getMessage());
        } catch (Exception e) {
            studentView.displayMessage(e.getMessage());
        }
    }

    public void searchStudent(String query) {
        try {
            List<StudentResponseDTO> responses = studentService.searchStudents(query);
            studentView.displayStudents(responses);
        } catch (Exception e) {
            studentView.displayMessage(e.getMessage());
        }
    }
}
