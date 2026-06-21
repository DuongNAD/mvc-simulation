## 2026-06-21T06:20:34Z
You are the Java Worker. Your working directory is e:\test\mvc-simulation\.agents\worker_java.
Your mission is to transition the Java codebase in `src/` from the Doctor mock scenario to the Student Management System mock scenario, implement the missing Service layer, ensure the codebase compiles cleanly, and clean up all obsolete voice assistant files from the workspace.

Detailed Requirements:
1. Rename and rewrite all Java code files in `src/` to match the Student Management System mock scenario:
   - Rename/rewrite DTOs: `src/dto/DoctorRequestDTO.java` -> `src/dto/StudentRequestDTO.java`, `src/dto/DoctorResponseDTO.java` -> `src/dto/StudentResponseDTO.java`.
   - Rename/rewrite Model: `src/model/Doctor.java` -> `src/model/Student.java` (fields: id, name, createdAt).
   - Rename/rewrite Repository: `src/repository/DoctorRepository.java` -> `src/repository/StudentRepository.java` (simulating database storage and CRUD queries for students).
   - Create Service layer: `src/service/StudentService.java` (performs business validations, name cannot be null/blank, and coordinates mapping between DTOs and models).
   - Rename/rewrite Controller: `src/controller/DoctorController.java` -> `src/controller/StudentController.java` (calls Service, uses View).
   - Rename/rewrite View: `src/view/DoctorView.java` -> `src/view/StudentView.java` (renders results to console).
   - Rewrite `src/main/Main.java`, `src/constants/Message.java`, `src/constants/Constants.java`, and `src/utils/Validation.java` to support the Student Management System menu (1. Add Student, 2. Delete Student, 3. Search Student, 4. Exit) and student logic.
   - Delete all old `.class` files under `src/` and any other build artifacts to ensure a clean source tree.
2. Clean up any obsolete voice assistant files in the workspace:
   - Delete the `voice_assistant/` directory and all files inside it.
   - Delete obsolete voice assistant test files in `tests/` (such as `test_optimization.py`, `test_rag.py`, `test_stt_llm.py`, `test_tts.py`, etc.) or any helper files (like `GiaiThichMVC.mp3`, `verify_stt_llm.py`, `verify_tts.py`, `sample_sheet.csv`, `sample_sheet.md`, `excel_output.txt`, `script.txt`, `Guide OOP Lab.xlsx`).
   - Leave only `run_tests.py` or new test files created by the Testing Track.
3. Verify that all Java files compile cleanly. Run a compilation test command (e.g., `javac -d bin src/**/*.java` or similar) through a compilation step and verify success.
4. Verify the backend works by running the compilable console app (e.g., input sample data, run a simulation pass if feasible).
