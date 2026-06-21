# BRIEFING — 2026-06-21T08:26:00+07:00

## Mission
Analyze the codebase and design a plan to verify the new R6 Hardware Optimization requirement in the E2E test suite.

## 🔒 My Identity
- Archetype: teamwork_preview_explorer
- Roles: teamwork_preview_explorer
- Working directory: e:\test\mvc-simulation\.agents\explorer_optimization_3
- Original parent: 0d442f36-4a15-41b8-84fa-0aee3b180d5c
- Milestone: R6 Hardware Optimization Verification

## 🔒 Key Constraints
- Read-only investigation — do NOT implement.
- Plan must comply with the requirement-driven, opaque-box testing philosophy.
- Check that no paid external APIs are required.

## Current Parent
- Conversation ID: 0d442f36-4a15-41b8-84fa-0aee3b180d5c
- Updated: not yet

## Investigation State
- **Explored paths**:
  - `voice_assistant/config.py` — Config variables.
  - `voice_assistant/stt.py` — Real STTEngine implementation details.
  - `voice_assistant/llm.py` — Real LLMEngine implementation details.
  - `voice_assistant/tts.py` — Real TTSEngine implementation details.
  - `tests/mock_assistant.py` — Mock structures, call history, sys.modules injection.
  - `tests/run_tests.py` — Discovery pattern for unittest.
  - `TEST_READY.md` — Current test coverage and execution log.
  - `TEST_INFRA.md` — Current test philosophy and feature inventory.
- **Key findings**:
  - Real STTEngine and LLMEngine models are loaded via constructor, lack `load_model()` and `unload_model()` functions.
  - The mock assistant does sys.modules patching for the whole voice_assistant stack under E2E tests, exposing mock classes to the E2E runner.
  - Adding `DYNAMIC_MODEL_LOADING` to `voice_assistant.config` is needed to toggle dynamic loading.
  - Mock engines must keep track of `_is_model_loaded`, devices, and block concurrent execution in VRAM.
- **Unexplored areas**:
  - Real implementation details of dynamic memory management in `AssistantController` (since `AssistantController` only exists in the mock file in the current version of the codebase).

## Key Decisions Made
- Support backward compatibility: keep `_is_model_loaded = True` by default in STTEngine/LLMEngine when `DYNAMIC_MODEL_LOADING` is `False`.
- Design a suite of 14 new test cases under Tiers 1-4 for `test_optimization.py`.

## Artifact Index
- e:\test\mvc-simulation\.agents\explorer_optimization_3\handoff.md — The main output report of this agent.
