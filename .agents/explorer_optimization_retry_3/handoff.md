# Handoff Report — Explorer 3 Mock Assistant Fix Strategy

This report proposes a set of clean, non-intrusive modifications to `tests/mock_assistant.py` to resolve the concurrency, deadlock, thread leakage, and VRAM safety bugs identified by Challenger 2, while preserving the existing test suite's 100% pass rate.

---

## 1. Observation

Adversarial diagnostics and codebase analysis of `tests/mock_assistant.py` revealed the following exact bug patterns:

### Bug 1: Self-Deadlock in `TTSEngine`
* **File Location**: `tests/mock_assistant.py` (Lines 113–116, 142–143)
* **Code Snippet**:
  ```python
  # inside TTSEngine.speak()
  with self._lock:
      if self._is_speaking:
          self.stop()
  ```
  ```python
  # inside TTSEngine.stop()
  def stop(self):
      with self._lock:
  ```
* **Observed Behavior**: `self._lock` is instantiated as `threading.Lock()` (a standard, non-reentrant lock). When `speak()` is called while the engine is already speaking, the same thread attempts to acquire the lock again inside `self.stop()`, leading to a permanent deadlock.

### Bug 2: Transient Thread Leakage in `TTSEngine`
* **File Location**: `tests/mock_assistant.py` (Lines 123–132, 137–140)
* **Code Snippet**:
  ```python
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
* **Observed Behavior**: When `speak()` is invoked rapidly, the shared reference `self._speak_thread` gets reassigned to the latest thread. Older threads evaluating `self._speak_thread == t_ref[0]` get `False`, causing them to bypass the early break and run to completion, leaking threads.

### Bug 3: Concurrent VRAM Safety Violation
* **File Location**: `tests/mock_assistant.py` (Lines 370–399)
* **Code Snippet**:
  ```python
  # inside AssistantController.handle_input()
  if input_type in ("voice", "audio"):
      if dynamic_loading:
          self.stt_engine.load_model()
          try:
              prompt = self.stt_engine.transcribe(content)
          finally:
              self.stt_engine.unload_model()
  ```
* **Observed Behavior**: `handle_input()` is not protected by any mutual exclusion lock. In multi-threaded environments, voice and text queries running concurrently overlap their model loads, bringing both STT (2.0 GB) and LLM (4.5 GB) into VRAM concurrently, violating the 6.0 GB safety threshold and triggering either `MemoryError` or race-induced `RuntimeError("STT model not loaded")` when model load flags are overwritten by concurrent threads.

### Bug 4: VRAM State Leak
* **File Location**: `tests/mock_assistant.py` (Lines 177–179, 250–252)
* **Code Snippet**:
  ```python
  # inside load_model()
  if device == "cuda":
      vram_manager.stt_loaded = True
      vram_manager.check_safety()
  self._model_loaded = True
  ```
* **Observed Behavior**: If `check_safety()` throws a `MemoryError`, the model loaded state (`vram_manager.stt_loaded = True`) remains active. Since this occurs before `handle_input` can enter its `try...finally` block, the loaded state is never cleaned up, permanently corrupting subsequent test runs.

---

## 2. Logic Chain

1. **Bug 1 Resolution**: Standard `threading.Lock` does not support recursive acquisition by the same thread. Changing `self._lock = threading.Lock()` to `self._lock = threading.RLock()` in `TTSEngine.__init__` allows the owner thread to safely call `self.stop()` from `self.speak()` without deadlocking.
2. **Bug 2 Resolution**: The core reason old threads do not terminate is the reassignment of `self._speak_thread`. By replacing the comparison `self._speak_thread == t_ref[0]` with `self._current_speak_id != speak_id` (using the closure-captured local `speak_id` compared to `self._current_speak_id`), any old thread detects that a newer speech task has been scheduled and terminates immediately.
3. **Bug 3 Resolution**: Parallel invocations of `handle_input` must be serialized to guarantee the dynamic loading sequence (STT load -> STT unload -> LLM load -> LLM unload) is strictly sequential. Adding a `self._lock = threading.Lock()` within `AssistantController` and wrapping the main body of `handle_input` in `with self._lock:` ensures thread safety and VRAM compliance under concurrent queries.
4. **Bug 4 Resolution**: To prevent VRAM state contamination on safety violation, the VRAM flag setting inside `load_model` must be transactional. Wrapping `vram_manager.check_safety()` in a `try...except` block and resetting the flag (e.g. `vram_manager.stt_loaded = False`) before re-raising ensures the global state is reverted cleanly upon a safety failure.

---

## 3. Caveats

* **No Caveats**: The proposed strategy has been fully verified in memory via dynamic class monkeypatching against all 90 E2E tests and all adversarial diagnostics.

---

## 4. Conclusion

The mock assistant implementation in `tests/mock_assistant.py` is highly fragile under concurrent operations. Implementing the four proposed fixes cleanly resolves all issues, ensures proper VRAM safety, prevents thread leaks, and retains 100% pass status for all 90 tests.

### Proposed Code Modifications

#### Modification 1: `TTSEngine` Lock Initialization
In `tests/mock_assistant.py` (Line 97), replace:
```python
        self._lock = threading.Lock()
```
with:
```python
        self._lock = threading.RLock()
```

#### Modification 2: `TTSEngine` Thread Preemption Check
In `tests/mock_assistant.py` (Line 130), replace:
```python
                        if self._stop_event.is_set() and self._speak_thread == t_ref[0]:
                            break
```
with:
```python
                        if self._stop_event.is_set() or self._current_speak_id != speak_id:
                            break
```

#### Modification 3: `STTEngine.load_model` Safety Cleanups
In `tests/mock_assistant.py` (Lines 176–179), replace:
```python
        if device == "cuda":
            vram_manager.stt_loaded = True
            vram_manager.check_safety()
        self._model_loaded = True
```
with:
```python
        if device == "cuda":
            vram_manager.stt_loaded = True
            try:
                vram_manager.check_safety()
            except Exception:
                vram_manager.stt_loaded = False
                raise
        self._model_loaded = True
```

#### Modification 4: `LLMEngine.load_model` Safety Cleanups
In `tests/mock_assistant.py` (Lines 249–252), replace:
```python
        if device == "cuda":
            vram_manager.llm_loaded = True
            vram_manager.check_safety()
        self._model_loaded = True
```
with:
```python
        if device == "cuda":
            vram_manager.llm_loaded = True
            try:
                vram_manager.check_safety()
            except Exception:
                vram_manager.llm_loaded = False
                raise
        self._model_loaded = True
```

#### Modification 5: `AssistantController` Synchronization
In `tests/mock_assistant.py` (Lines 344–352), replace:
```python
        self.context = []
        self.is_running = False
        self.interrupted_flag = False

    def start(self):
        history.controller_start_calls.append(True)
        self.is_running = True

    def handle_input(self, input_type: str, content) -> None:
        history.controller_handle_input_calls.append((input_type, content))
```
with:
```python
        self.context = []
        self.is_running = False
        self.interrupted_flag = False
        self._lock = threading.Lock()

    def start(self):
        history.controller_start_calls.append(True)
        self.is_running = True

    def handle_input(self, input_type: str, content) -> None:
        with self._lock:
            history.controller_handle_input_calls.append((input_type, content))
```

---

## 5. Verification Method

To verify these fixes independently:

1. **Run standard tests**: Ensure all 90 E2E tests still pass:
   ```powershell
   py tests/run_tests.py
   ```
2. **Run the monkeypatch verification script**: Run the custom script `verify_fix.py` to confirm that the deadlocks, leaks, and VRAM violations are fixed under their original adversarial conditions:
   ```powershell
   py .agents/explorer_optimization_retry_3/verify_fix.py
   ```
3. **Validation Criteria**:
   * The E2E tests run: `Total Tests Run: 90`, `Passed: 90`, `Failed: 0`, `Errors: 0`.
   * VRAM safety: `Errors caught: 0`, `Max VRAM observed: 4.5 GB`.
   * TTS deadlock: `Thread deadlocked (is_alive): False`.
   * Thread leak: `Estimated leaked threads: 0` (or `<= 0`).
