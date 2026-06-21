## 2026-06-21T01:26:26Z
You are Worker 1, a coding and implementation agent.
Your working directory is e:\test\mvc-simulation\.agents\worker_optimization_1.
Your identity: Worker 1 (role: teamwork_preview_worker)

Objective:
Implement the R6 Hardware Optimization E2E test changes based on the reconciled Explorer handoff reports.

MANDATORY INTEGRITY WARNING — DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Steps to execute:

1. Update `tests/mock_assistant.py`:
   - Expand `MockHistory` to track loaded/unloaded call history for STT and LLM models. Add fields `stt_load_calls`, `stt_unload_calls`, `llm_load_calls`, `llm_unload_calls`.
   - Update `reset_history()` to clear these lists and reset the VRAM manager.
   - Introduce a module-level `loaded_in_vram = set()` and `MockVRAMManager` to simulate VRAM usage. The `MockVRAMManager` should:
     * Track if `stt_loaded` and `llm_loaded` are active.
     * Enforce a 6.0 GB VRAM limit. STT uses 2.0 GB of VRAM on CUDA, LLM uses 4.5 GB on CUDA. If VRAM exceeds 6.0 GB, raise a `MemoryError`.
   - Add `load_model()` and `unload_model()` methods to both `STTEngine` and `LLMEngine`. In `load_model()`, check device configs. If device is `"cuda"`, set the loaded status in `vram_manager` and check safety (raising `MemoryError` if VRAM is exceeded).
   - In `STTEngine.__init__` and `LLMEngine.__init__`, if `DYNAMIC_MODEL_LOADING` config is False, automatically call `load_model()` to maintain backward compatibility. If it is True, do not load model during initialization.
   - Update `transcribe()` and `generate_response()` to check if the model is loaded when `DYNAMIC_MODEL_LOADING` is active, throwing `RuntimeError` if not loaded.
   - Update `AssistantController.handle_input()` to orchestrate the dynamic model loading schedule if `DYNAMIC_MODEL_LOADING` is enabled. Use `try...finally` to guarantee model unloading in case of exceptions.
   - Update the configuration overrides at the bottom of `tests/mock_assistant.py` to add baseline variables:
     * `va_config.DYNAMIC_MODEL_LOADING = False`
     * `va_config.STT_DEVICE = "cuda"`
     * `va_config.LLM_DEVICE = "cuda"`
     * `va_config.TTS_DEVICE = "cpu"`

2. Create `tests/test_optimization.py`:
   - Create this file and implement the 15 test cases (Tiers 1-4) verifying happy paths, edge cases, cross-features, and real-world scenarios. Make sure it imports `tests.mock_assistant` first.

3. Update `tests/run_tests.py`:
   - Add discovery for `test_optimization.py` and merge it into the running test suite.

4. Revise `TEST_INFRA.md`:
   - Document the new optimization feature details, test files, and update Section 5 Coverage Thresholds to reflect the new 90 tests.

5. Update `TEST_READY.md`:
   - Run the updated test runner `tests/run_tests.py` using `run_command` or tests executor, verify 90/90 tests pass.
   - Update `TEST_READY.md` with the new test counts, verification logs, and status showing 90/90 tests passing.

Verify that all 90 tests pass and layout compliance is met before presenting your handoff.
