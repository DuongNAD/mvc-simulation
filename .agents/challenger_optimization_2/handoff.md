# Handoff Report — Hardware Optimization Adversarial Verification

## 1. Observation
Adversarial verification was performed by creating a targeted test suite and executing it using the python interpreter.
- **Test File Path**: `tests/test_optimization_adversarial.py`
- **Runner File Path**: `tests/run_adversarial_diagnostics.py`
- **Implementation File Path**: `tests/mock_assistant.py`

### Diagnostic Outputs
Command executed: `py tests/run_adversarial_diagnostics.py`
Output:
```
test_concurrent_dynamic_loading_vram_violation (test_optimization_adversarial.TestAdversarialOptimization.test_concurrent_dynamic_loading_vram_violation)
Adversarial Test 1: Concurrency and VRAM Safety Violation. ... ok

----------------------------------------------------------------------
Ran 1 test in 0.021s

OK
test_tts_engine_reentrant_lock_deadlock (test_optimization_adversarial.TestAdversarialOptimization.test_tts_engine_reentrant_lock_deadlock)
Adversarial Test 2: Reentrant Lock Deadlock in TTSEngine. ... ok

----------------------------------------------------------------------
Ran 1 test in 1.006s

OK
test_tts_thread_and_task_leak (test_optimization_adversarial.TestAdversarialOptimization.test_tts_thread_and_task_leak)
Adversarial Test 3: Thread and Task Leakage in TTSEngine. ... ok

----------------------------------------------------------------------
Ran 1 test in 0.686s

OK
Running test_concurrent_dynamic_loading_vram_violation...

--- VRAM Concurrency Test Summary ---
Total errors caught: 1
MemoryError count: 1
test_concurrent_dynamic_loading_vram_violation finished. Success: True

Running test_tts_engine_reentrant_lock_deadlock...

--- TTS Deadlock Test Summary ---
Thread deadlocked (is_alive): True
test_tts_engine_reentrant_lock_deadlock finished. Success: True

Running test_tts_thread_and_task_leak...

--- TTS Thread Leak Test Summary ---
Initial threads: 3
Active run_speak threads count: 16
test_tts_thread_and_task_leak finished. Success: True
```

## 2. Logic Chain
1. **Self-Deadlock in TTSEngine**: In `tests/mock_assistant.py` (lines 113-116), calling `speak()` while `_is_speaking` is `True` invokes `self.stop()` under the protection of `self._lock`:
   ```python
   with self._lock:
       if self._is_speaking:
           self.stop()
   ```
   However, `self.stop()` (lines 142-143) attempts to acquire the exact same lock:
   ```python
   def stop(self):
       with self._lock:
   ```
   Since `self._lock` is a standard `threading.Lock` (non-reentrant), this causes an immediate deadlock on the main thread, freezing the execution when any speech interrupts another.
2. **Transient Thread Leakage**: In `tests/mock_assistant.py` (lines 130-131), the spawned thread checks for cancellation via:
   ```python
   if self._stop_event.is_set() and self._speak_thread == t_ref[0]:
       break
   ```
   When `speak()` is called in rapid succession, `self._speak_thread` is reassigned to the latest thread. This causes the comparison `self._speak_thread == t_ref[0]` to evaluate to `False` for all older threads. Consequently, old threads ignore the stop event, continuing to sleep and run until their full duration expires, leaking CPU/thread resources.
3. **VRAM Safety Concurrency Violation**: In `tests/mock_assistant.py` (lines 351-414), `AssistantController.handle_input` performs sequential model loading/unloading without any cross-thread serialization:
   - Thread A (voice query) loads STT.
   - Thread B (text query) starts concurrently and loads LLM.
   - Both models reside in VRAM concurrently (`loaded_in_vram = {"stt", "llm"}`), resulting in 6.5 GB occupancy, which exceeds the 6.0 GB threshold.
   - This raises `MemoryError` and crashes the scheduler because the sequential unloading guarantee is violated under concurrency.
4. **VRAM State/Reference Leaks**: If `load_model()` fails its safety check and raises `MemoryError`, it does so before the caller can enter the `try...finally` block that cleans up the model. Thus, the model is left registered in `loaded_in_vram` indefinitely, polluting subsequent executions.

## 3. Caveats
- These findings apply to the simulation layer (`tests/mock_assistant.py`) used in the project's test suite.
- The real implementations (`voice_assistant/stt.py` and `voice_assistant/llm.py`) do not yet contain dynamic loading mechanisms. Therefore, the actual models are loaded once at startup and are not subject to these dynamic scheduling issues, but they do lack the ability to run on low-memory devices where dynamic loading is required.

## 4. Conclusion
- **Verdict: FAIL**
- The Hardware Optimization scheduler is highly fragile and fails under concurrent operations. To make it robust:
  1. Replace `threading.Lock` with `threading.RLock` in `TTSEngine` to prevent self-deadlocks.
  2. Implement mutual exclusion locks in `AssistantController` to serialize model loading and execution steps across threads.
  3. Fix the preemption thread identity check in `TTSEngine` (e.g. check the `speak_id` rather than thread references) to avoid thread leaks.

## 5. Verification Method
1. Set the environment variable `MOCK_ENGINES=1`.
2. Run the command:
   ```powershell
   py tests/run_adversarial_diagnostics.py
   ```
3. Inspect `tests/test_optimization_adversarial.py` to review the test scenarios (deterministic VRAM overlap, deadlock detection, and RLock-patched thread-leak counting).
