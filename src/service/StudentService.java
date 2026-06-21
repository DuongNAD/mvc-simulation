package service;

import constants.Message;
import dto.StudentRequestDTO;
import dto.StudentResponseDTO;
import model.Student;
import repository.StudentRepository;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

public class StudentService {
    private final StudentRepository studentRepository;
    private final DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    public StudentService(StudentRepository studentRepository) {
        this.studentRepository = studentRepository;
    }

    public StudentResponseDTO addStudent(StudentRequestDTO requestDTO) throws Exception {
        // Business Validation: Name cannot be null or blank
        if (requestDTO == null || requestDTO.getName() == null || requestDTO.getName().trim().isEmpty()) {
            throw new Exception(Message.EMPTY_INPUT);
        }

        // Coordinates mapping between DTOs and models
        Student student = new Student();
        student.setName(requestDTO.getName().trim());
        student.setCreatedAt(LocalDateTime.now().format(formatter));

        // Persist via Repository
        Student savedStudent = studentRepository.save(student);

        // Map model back to Response DTO
        String displayString = String.format("%-10d%-25s%-25s", 
                savedStudent.getId(), savedStudent.getName(), savedStudent.getCreatedAt());
        
        return new StudentResponseDTO(
                savedStudent.getId(),
                "Student added successfully.",
                displayString
        );
    }

    public StudentResponseDTO deleteStudent(int id) throws Exception {
        // Business Validation: Student must exist
        Student existing = studentRepository.findById(id);
        if (existing == null) {
            throw new Exception(Message.NO_STUDENT_AVAILABLE);
        }

        studentRepository.delete(id);

        String displayString = String.format("%-10d%-25s%-25s", 
                existing.getId(), existing.getName(), existing.getCreatedAt());

        return new StudentResponseDTO(
                id,
                "Student deleted successfully.",
                displayString
        );
    }

    public List<StudentResponseDTO> searchStudents(String query) throws Exception {
        // Business Validation: Check if repository is empty
        if (studentRepository.isEmpty()) {
            throw new Exception(Message.DATABASE_EMPTY);
        }

        List<Student> students = studentRepository.searchByName(query);
        if (students.isEmpty()) {
            throw new Exception(Message.NO_STUDENT_AVAILABLE);
        }

        List<StudentResponseDTO> responses = new ArrayList<>();
        for (Student s : students) {
            String displayString = String.format("%-10d%-25s%-25s", 
                    s.getId(), s.getName(), s.getCreatedAt());
            responses.add(new StudentResponseDTO(s.getId(), "Found", displayString));
        }
        return responses;
    }
}
