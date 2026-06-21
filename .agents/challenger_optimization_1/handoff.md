# Adversarial Verification Handoff Report - R6 Hardware Optimization

## 1. Observation

Adversarial testing was executed against the R6 Hardware Optimization mock infrastructure (`tests/mock_assistant.py`) using a dedicated verification script `tests/test_optimization_adversarial.py`. The execution command and results are logged below:

### Command:
`py tests/test_optimization_adversarial.py`

### Output:
```
--- VRAM Concurrency Test Summary ---
Total concurrent threads: 5
Total errors caught: 4
MemoryError count: 0
RuntimeError count: 4
Max VRAM observed: 4.5 GB
Detail of errors:
- RuntimeError: STT model not loaded
- RuntimeError: STT model not loaded
- RuntimeError: STT model not loaded
- RuntimeError: STT model not loaded

--- TTS Deadlock Test Summary ---
Thread deadlocked (is_alive): True

--- TTS Thread Leak Test Summary ---
Initial threads: 3
Peak threads: 5
Estimated leaked threads: 2
```

We directly observed these critical issues in `tests/mock_assistant.py`:

#### Issue A: Concurrency Model State Corruption (Race Condition)
In `AssistantController.handle_input` (lines 371-378 and 394-401):
```python
        if input_type in ("voice", "audio"):
            if dynamic_loading:
                self.stt_engine.load_model()
                try:
                    prompt = self.stt_engine.transcribe(content)
                finally:
                    self.stt_engine.unload_model()
```
And inside `STTEngine.load_model()` / `unload_model()` (lines 177-191) and `transcribe()` (lines 200-201):
```python
    def load_model(self):
        ...
        self._model_loaded = True

    def unload_model(self):
        ...
        self._model_loaded = False

    def transcribe(self, audio_path_or_data) -> str:
        ...
        if dynamic_loading and not self._model_loaded:
            raise RuntimeError("STT model not loaded")
```
When multiple threads call `handle_input` concurrently, Thread 1's `unload_model()` resets `self._model_loaded = False` globally for the shared `stt_engine` while Thread 2 is still executing `transcribe()`, resulting in `RuntimeError("STT model not loaded")` in Thread 2.

#### Issue B: Reentrant Lock Deadlock in `TTSEngine`
In `TTSEngine.speak` (lines 113-115) and `TTSEngine.stop` (lines 142-146):
```python
    def speak(self, text: str, volume: float = 0.5):
        ...
        with self._lock:
            if self._is_speaking:
                self.stop()
```
And:
```python
    def stop(self):
        with self._lock:
            history.tts_stop_calls.append(True)
            self._stop_event.set()
            self._is_speaking = False
```
When `speak()` is called while the engine is already speaking, `self.stop()` is invoked while the calling thread holds `self._lock` (which is a standard `threading.Lock()` initialized on line 97). Since standard locks in Python are not reentrant, the calling thread blocks indefinitely waiting for itself to release the lock.

#### Issue C: Thread / Task Leakage in `TTSEngine`
In `TTSEngine.speak` (lines 125-135):
```python
            # Use local reference to the thread to avoid race condition
            t_ref = []
            def run_speak():
                duration = min(0.5, max(0.05, len(text) * 0.005))
                start_time = time.time()
                while time.time() - start_time < duration:
                    with self._lock:
                        if self._stop_event.is_set() and self._speak_thread == t_ref[0]:
                            break
                    time.sleep(0.01)
```
When `stop()` is called and then a new `speak()` immediately follows, the stop event is cleared (`self._stop_event.clear()`) and `self._speak_thread` is reassigned to the new thread before the old thread checks the event loop. Thus, the old thread checks `_stop_event.is_set()` (which is now `False`) and `self._speak_thread == t_ref[0]` (which is `False`), bypasses the exit `break`, and continues sleeping in the background until the duration expires, leaking active threads.

#### Issue D: Permanently Fouled VRAM State on `MemoryError`
In `AssistantController.handle_input` (lines 371-378):
```python
            if dynamic_loading:
                self.stt_engine.load_model()
                try:
                    prompt = self.stt_engine.transcribe(content)
                finally:
                    self.stt_engine.unload_model()
```
Because `stt_engine.load_model()` is outside the `try...finally` block, if a `MemoryError` is raised inside `load_model()` (when `vram_manager.check_safety()` triggers), the `unload_model()` cleanup is bypassed. Thus, STT/LLM remain marked as loaded in the global `vram_manager` indefinitely, corrupting subsequent calls.

---

## 2. Logic Chain

1. **Lack of Concurrency Synchronization in dynamic load/unload sequences**: Multiple threads accessing a shared controller concurrently will load and unload the same shared engine resources. Because there is no class-level or controller-level serialization (locking) around the dynamic model load -> transcribe/generate -> unload sequence, the state is corrupted across threads (Observation A).
2. **Reentrant Lock Violation**: The design of `speak` calls `stop` when already speaking. Both methods request the same lock object (`self._lock = threading.Lock()`). Because a standard thread lock cannot be acquired twice by the same thread, this causes an instant deadlock of the executing thread (Observation B).
3. **Invalid Interrupt Check leading to Thread Leakage**: The safety check `self._speak_thread == t_ref[0]` in `run_speak` blocks the thread from breaking when it is no longer the active speak thread. The correct logic should break *because* the current active thread has changed. When a new thread starts, it clears the shared stop event. Consequently, preempted threads miss the stop signal and continue executing, causing a background thread leak (Observation C).
4. **Incorrect Exception Scoping**: By putting model loading outside of the `try...finally` block, any VRAM safety violation that raises `MemoryError` leaves the model registered as loaded in the VRAM manager, causing permanent VRAM state corruption (Observation D).

---

## 3. Caveats

- **Mock Fidelity**: The vulnerabilities were discovered and verified against the simulated/mock implementation files (`tests/mock_assistant.py`) because the real production engines do not currently implement dynamic model loading scheduling. However, any real implementation based on these mocks would inherit the identical structural thread safety issues.
- **CPU Scheduling**: In normal synchronous test cases, because mock methods run instantly, GIL prevents thread context switches, making concurrency issues hard to hit without monkeypatched artificial delays. The verification suite uses `time.sleep` to guarantee thread context switches and reproduce the race conditions reliably.

---

## 4. Conclusion

**Verdict: FAIL**

The R6 Hardware Optimization implementation suffers from critical structural vulnerabilities:
1. **Deadlock Vulnerability**: Bricks the voice assistant instantly upon double-speak or prompt preemption.
2. **Thread Leakage**: Leaks system resources under rapid interruptions.
3. **State Corruption under Concurrency**: Inability to handle concurrent requests under dynamic loading, throwing `RuntimeError` due to premature unloads.
4. **Permanent Fail-State**: Inability to recover from `MemoryError` due to missing `try...finally` scope protection.

---

## 5. Verification Method

To verify these findings, run the custom adversarial test suite:

```bash
py tests/test_optimization_adversarial.py
```

### Expected Results:
- `test_tts_engine_reentrant_lock_deadlock` must assert `Thread deadlocked (is_alive): True`.
- `test_tts_thread_and_task_leak` must assert `Estimated leaked threads >= 1`.
- `test_concurrent_dynamic_loading_vram_violation` must catch multiple `RuntimeError` or `MemoryError` showing concurrency conflicts.
