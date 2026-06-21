# BRIEFING — 2026-06-21T08:40:00+07:00

## Mission
Analyze concurrency, deadlock, and thread leak bugs identified by Challenger 2, and design a plan to fix them in tests/mock_assistant.py.

## 🔒 My Identity
- Archetype: teamwork_preview_explorer
- Roles: Explorer 1, teamwork_preview_explorer
- Working directory: e:\test\mvc-simulation\.agents\explorer_optimization_retry_1
- Original parent: 0d442f36-4a15-41b8-84fa-0aee3b180d5c
- Milestone: Optimization bug resolution

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Verify that your proposed fix strategy complies with the requirement-driven, opaque-box testing philosophy.
- Code-only network mode (no external web access).

## Current Parent
- Conversation ID: 0d442f36-4a15-41b8-84fa-0aee3b180d5c
- Updated: 2026-06-21T08:40:00+07:00

## Investigation State
- **Explored paths**:
  - `tests/mock_assistant.py` (Mock Implementation)
  - `tests/test_optimization.py` (Standard E2E optimization test suite)
  - `tests/test_optimization_adversarial.py` (Adversarial test suite)
  - `.agents/challenger_optimization_2/handoff.md` (Challenger report)
- **Key findings**:
  - **Self-Deadlock**: TTSEngine.speak() calls self.stop() under a standard non-reentrant Lock, causing deadlock. Solved by replacing it with RLock.
  - **Thread Leakage**: Thread cancellation checks thread handles which change when `self._speak_thread` is reassigned. Solved by checking `self._current_speak_id != speak_id`.
  - **Concurrent VRAM Safety Violation**: Concurrent queries load STT and LLM models at the same time, violating the VRAM limit. Solved by serializing `handle_input` in `AssistantController` using a reentrant lock.
  - **VRAM State Leak**: Exceptions in `load_model()` prevent cleanup because the caller's `try...finally` block is never entered. Solved by reverting VRAM registration state inside `load_model()`'s exception handler.
- **Unexplored areas**: None

## Key Decisions Made
- Serialize `AssistantController.handle_input` to avoid concurrent dynamic model loading.
- Use `threading.RLock` for reentrant locks in `TTSEngine` and `AssistantController`.
- Identify preempted speak tasks using monotonic IDs (`self._current_speak_id != speak_id`) rather than thread comparisons.
- Wrap model registration safety checks in a try-except block inside `load_model()` to prevent VRAM state leak.

## Artifact Index
- e:\test\mvc-simulation\.agents\explorer_optimization_retry_1\handoff.md — Analysis and proposed fixes report
