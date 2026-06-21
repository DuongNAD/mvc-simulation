package repository;

import model.Student;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class StudentRepository {
    private final Map<Integer, Student> studentMap = new HashMap<>();
    private int nextId = 1;

    public StudentRepository() {
    }

    public Student save(Student student) {
        if (student.getId() <= 0) {
            student.setId(nextId++);
        }
        studentMap.put(student.getId(), student);
        return student;
    }

    public boolean delete(int id) {
        if (studentMap.containsKey(id)) {
            studentMap.remove(id);
            return true;
        }
        return false;
    }

    public Student findById(int id) {
        return studentMap.get(id);
    }

    public List<Student> searchByName(String query) {
        List<Student> result = new ArrayList<>();
        String lowerQuery = query.toLowerCase();
        for (Student s : studentMap.values()) {
            if (s.getName().toLowerCase().contains(lowerQuery)) {
                result.add(s);
            }
        }
        return result;
    }

    public boolean isEmpty() {
        return studentMap.isEmpty();
    }

    public List<Student> getAll() {
        return new ArrayList<>(studentMap.values());
    }
}
