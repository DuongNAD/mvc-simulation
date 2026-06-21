# Scope: Implementation Track for Java MVC Educational Simulation

## Architecture
The application is an educational simulation explaining Model-View-Controller (MVC) architecture.
- **Frontend (`index.html`)**: An interactive page showing data flow (View ↔ Controller ↔ Service ↔ Repository ↔ Model). Needs manual controls and Java code reference integration.
- **Backend (`src/`)**: Compilable Java CLI matching Student Management System.
  - Controller ↔ Service ↔ Repository ↔ Model

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Manual Stepping UI | Add Next/Prev buttons in `index.html`, transition state machine, database rollback on step 5 -> 4. | None | DONE |
| 2 | Code Snippets & Copy Tab | Embed Java snippets for each step, add full reference code view and copy buttons in `index.html`. | M1 | DONE |
| 3 | Java Scenario Rewrite | Rename and rewrite all Java files in `src/` to Student scenario and implement `StudentService.java`. | None | DONE |
| 4 | Obsolete Files Cleanup | Delete all files in `voice_assistant/` and old assistant-related test files in `tests/`. | None | DONE |
| 5 | E2E Verification | Run Pytest test suite when Testing Track publishes `TEST_READY.md` and ensure 100% pass rate. | M1, M2, M3, M4 | DONE |

## Interface Contracts
### StudentRequestDTO
- `String getName()` / `void setName(String name)`
### StudentResponseDTO
- `int getId()`, `String getMessage()`, `String getDisplayString()`
### StudentController
- `void addStudent(StudentRequestDTO requestDTO)` -> Calls Service layer to validate and persist.
- `void deleteStudent(int id)` -> Calls Service layer to remove.
- `void searchStudent(String query)` -> Calls Service to find and triggers View display.
### StudentService
- Validates name input (cannot be blank/empty).
- Coordinates between Controller DTOs and Repository entities.
