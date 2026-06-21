package tests;

import constants.Message;
import dto.StudentRequestDTO;
import dto.StudentResponseDTO;
import repository.StudentRepository;
import service.StudentService;
import java.util.List;

public class StudentServiceTest {

    public static void main(String[] args) {
        try {
            System.out.println("Running Java StudentService Validation Tests...");
            testAddStudentValid();
            testAddStudentEmpty();
            testAddStudentBlank();
            testAddStudentNull();
            testDeleteStudentValid();
            testDeleteStudentNonExistent();
            testDeleteStudentNegativeId();
            testSearchStudentsEmptyDb();
            testSearchStudentsNoMatch();
            testSearchStudentsValid();
            System.out.println("ALL JAVA BACKEND TESTS PASSED!");
        } catch (Throwable t) {
            System.err.println("TEST FAILED!");
            t.printStackTrace();
            System.exit(1);
        }
    }

    private static void assertEquals(Object expected, Object actual, String message) {
        if (expected == null && actual == null) return;
        if (expected != null && expected.equals(actual)) return;
        throw new AssertionError(message + " - Expected: " + expected + ", Actual: " + actual);
    }

    private static void assertNotNull(Object obj, String message) {
        if (obj == null) {
            throw new AssertionError(message + " - Expected not null");
        }
    }

    private static void fail(String message) {
        throw new AssertionError(message);
    }

    // 1. Add Student Valid
    private static void testAddStudentValid() throws Exception {
        StudentRepository repo = new StudentRepository();
        StudentService service = new StudentService(repo);
        StudentRequestDTO req = new StudentRequestDTO("Tran Van A");
        StudentResponseDTO res = service.addStudent(req);
        
        assertNotNull(res, "Response should not be null");
        assertEquals(1, res.getId(), "First student should have ID 1");
        assertEquals("Student added successfully.", res.getMessage(), "Success message mismatch");
        assertNotNull(res.getDisplayString(), "Display string should not be null");
    }

    // 2. Add Student Empty Name
    private static void testAddStudentEmpty() {
        StudentRepository repo = new StudentRepository();
        StudentService service = new StudentService(repo);
        StudentRequestDTO req = new StudentRequestDTO("");
        try {
            service.addStudent(req);
            fail("Should have thrown Exception for empty name");
        } catch (Exception e) {
            assertEquals(Message.EMPTY_INPUT, e.getMessage(), "Exception message mismatch");
        }
    }

    // 3. Add Student Blank Name
    private static void testAddStudentBlank() {
        StudentRepository repo = new StudentRepository();
        StudentService service = new StudentService(repo);
        StudentRequestDTO req = new StudentRequestDTO("   ");
        try {
            service.addStudent(req);
            fail("Should have thrown Exception for blank name");
        } catch (Exception e) {
            assertEquals(Message.EMPTY_INPUT, e.getMessage(), "Exception message mismatch");
        }
    }

    // 4. Add Student Null Name
    private static void testAddStudentNull() {
        StudentRepository repo = new StudentRepository();
        StudentService service = new StudentService(repo);
        StudentRequestDTO req = new StudentRequestDTO(null);
        try {
            service.addStudent(req);
            fail("Should have thrown Exception for null name");
        } catch (Exception e) {
            assertEquals(Message.EMPTY_INPUT, e.getMessage(), "Exception message mismatch");
        }
    }

    // 5. Delete Student Valid
    private static void testDeleteStudentValid() throws Exception {
        StudentRepository repo = new StudentRepository();
        StudentService service = new StudentService(repo);
        StudentRequestDTO req = new StudentRequestDTO("Tran Van A");
        StudentResponseDTO addRes = service.addStudent(req);
        
        StudentResponseDTO delRes = service.deleteStudent(addRes.getId());
        assertNotNull(delRes, "Delete response should not be null");
        assertEquals(addRes.getId(), delRes.getId(), "Deleted ID should match");
        assertEquals("Student deleted successfully.", delRes.getMessage(), "Delete message mismatch");
    }

    // 6. Delete Non-existent Student
    private static void testDeleteStudentNonExistent() {
        StudentRepository repo = new StudentRepository();
        StudentService service = new StudentService(repo);
        try {
            service.deleteStudent(999);
            fail("Should have thrown Exception for deleting non-existent student");
        } catch (Exception e) {
            assertEquals(Message.NO_STUDENT_AVAILABLE, e.getMessage(), "Exception message mismatch");
        }
    }

    // 7. Delete negative/zero ID
    private static void testDeleteStudentNegativeId() {
        StudentRepository repo = new StudentRepository();
        StudentService service = new StudentService(repo);
        try {
            service.deleteStudent(-5);
            fail("Should have thrown Exception for negative ID deletion");
        } catch (Exception e) {
            assertEquals(Message.NO_STUDENT_AVAILABLE, e.getMessage(), "Exception message mismatch");
        }
    }

    // 8. Search Students on Empty DB
    private static void testSearchStudentsEmptyDb() {
        StudentRepository repo = new StudentRepository();
        StudentService service = new StudentService(repo);
        try {
            service.searchStudents("A");
            fail("Should have thrown Exception when searching empty DB");
        } catch (Exception e) {
            assertEquals(Message.DATABASE_EMPTY, e.getMessage(), "Exception message mismatch");
        }
    }

    // 9. Search Students with no matches
    private static void testSearchStudentsNoMatch() throws Exception {
        StudentRepository repo = new StudentRepository();
        StudentService service = new StudentService(repo);
        service.addStudent(new StudentRequestDTO("Tran Van A"));
        try {
            service.searchStudents("NonExistentName");
            fail("Should have thrown Exception when no match is found");
        } catch (Exception e) {
            assertEquals(Message.NO_STUDENT_AVAILABLE, e.getMessage(), "Exception message mismatch");
        }
    }

    // 10. Search Students successfully
    private static void testSearchStudentsValid() throws Exception {
        StudentRepository repo = new StudentRepository();
        StudentService service = new StudentService(repo);
        service.addStudent(new StudentRequestDTO("Tran Van A"));
        service.addStudent(new StudentRequestDTO("Nguyen Van B"));
        
        List<StudentResponseDTO> results = service.searchStudents("Van");
        assertEquals(2, results.size(), "Should find 2 students with 'Van'");
        
        List<StudentResponseDTO> resultsB = service.searchStudents("B");
        assertEquals(1, resultsB.size(), "Should find 1 student with 'B'");
        assertEquals(2, resultsB.get(0).getId(), "Found student ID should be 2");
    }
}
