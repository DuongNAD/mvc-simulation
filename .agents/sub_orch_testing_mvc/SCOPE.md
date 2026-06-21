# Scope: E2E Testing Track

## Architecture
The application features a frontend simulation (`index.html`) using a step-by-step state machine (Steps 0-7) to visualize the MVC pattern (Main, Controller, Service, Repository, Model/Database, View). The test suite verifies DOM states, navigation, visual transitions, and database state.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Test Plan & Discovery | Define 4-tier test case scenarios, map target elements in `index.html`, and identify files to delete. | None | DONE |
| 2 | Clean Obsolete Files | Delete all existing voice assistant tests and related scripts in `tests/`. | M1 | DONE |
| 3 | E2E Test Suite Implementation | Create `tests/test_mvc_flow.py` using Playwright, covering Tier 1-4 scenarios. | M2 | DONE |
| 4 | Test Runner Implementation | Create `tests/run_tests.py` to discover and execute pytest with Chromium. | M3 | DONE |
| 5 | Documentation | Create `TEST_INFRA.md` and `TEST_READY.md` in the project root. | M4 | DONE |

## Interface Contracts
- Input fields: `#studentName` (input), `#startBtn` (button)
- Controls: `#simulation-controls` (div), `#prevBtn` (button), `#nextBtn` (button)
- Active layer boxes: `.layer-box.active`
- Active connecting arrows: `.arrow-down.active`, `.arrow-up.active`
- Display elements: `#database-content` (pre), `#console-output` (div), `#payload-display` (pre)
