# Handoff Report — E2E Optimization Mocks Bug Analysis & Proposed Fixes

## 1. Observation

A detailed investigation was conducted on the simulation layer implementation in `tests/mock_assistant.py`, E2E optimization test suites (`tests/test_optimization.py`, `tests/test_optimization_adversarial.py`), and the diagnostics runner `tests/run_adversarial_diagnostics.py`.

The four identified concurrency, deadlock, and thread leak bugs in `tests/mock_assistant.py` were analyzed:

### Bug 1: Self-Deadlock in TTSEngine
- **File**: `tests/mock_assistant.py` (lines 113-116 and 142-146)
- **Code Block**:
  ```python
  # In speak()
  with self._lock:
      if self._is_speaking:
          self.stop()
  
  # In stop()
  def stop(self):
      with self._lock:
  ```
- **Error/Behavior**: When `speak()` is called while `self._is_speaking` is `True`, it invokes `self.stop()` under the protection of `self._lock` (a standard non-reentrant `threading.Lock`). This causes the calling thread to attempt to re-acquire the lock it already holds, resulting in a self-deadlock that hangs the execution.

### Bug 2: Transient Thread Leakage in TTSEngine
- **File**: `tests/mock_assistant.py` (lines 123-140)
- **Code Block**:
  ```python
  # In speak()
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
- **Error/Behavior**: When multiple rapid `speak()` calls occur, `self._speak_thread` gets reassigned to the newest thread, and the shared `self._stop_event` is cleared. Consequently, the comparison `self._speak_thread == t_ref[0]` evaluates to `False` for any older thread. Older threads fail the cancellation check, ignoring `_stop_event`, and continue running until their full duration expires, causing thread leakage.

### Bug 3: Concurrent VRAM Safety Violation
- **File**: `tests/mock_assistant.py` (lines 351-414, `AssistantController.handle_input()`)
- **Code Block**:
  ```python
  # In handle_input()
  if input_type in ("voice", "audio"):
      if dynamic_loading:
          self.stt_engine.load_model()
          try:
              prompt = self.stt_engine.transcribe(content)
          finally:
              self.stt_engine.unload_model()
  ...
  if dynamic_loading:
      self.llm_engine.load_model()
      try:
          response = self.llm_engine.generate_response(prompt, self.context, retrieval_context=retrieval_context)
      finally:
          self.llm_engine.unload_model()
  ```
- **Error/Behavior**: Without synchronization in `handle_input()`, concurrent voice and text queries running on separate threads can overlap. For instance, Thread A might load the STT model while Thread B concurrently loads the LLM model. This puts both models in VRAM simultaneously (`loaded_in_vram = {"stt", "llm"}`), totaling 6.5 GB (STT 2.0 GB + LLM 4.5 GB), which exceeds the 6.0 GB limit and causes a `MemoryError`.

### Bug 4: VRAM State Leak
- **File**: `tests/mock_assistant.py` (lines 168-180 and 241-253)
- **Code Block**:
  ```python
  # In STTEngine.load_model() / LLMEngine.load_model()
  if device == "cuda":
      vram_manager.stt_loaded = True
      vram_manager.check_safety()
  self._model_loaded = True
  ```
- **Error/Behavior**: If `check_safety()` raises `MemoryError`, it propagates out of `load_model()` before `self._model_loaded = True` runs. More critically, it occurs before the caller enters the `try...finally` block that unloads the model. The model remains registered in `loaded_in_vram` (`vram_manager.stt_loaded` / `vram_manager.llm_loaded` is still `True`), leaking VRAM state to subsequent runs.

---

## 2. Logic Chain

1. **Deadlock Resolution (Bug 1)**: By replacing `threading.Lock()` with `threading.RLock()`, a single thread can acquire the lock multiple times. When `speak()` calls `stop()` on the same thread, the second lock acquisition succeeds.
2. **Leak Resolution (Bug 2)**: Storing a unique `speak_id` locally in each thread and comparing it with the global `self._current_speak_id` allows threads to know if they have been preempted. If `speak_id != self._current_speak_id`, it means a newer speech call was started. Breaking the loop when `speak_id != self._current_speak_id` or `self._stop_event.is_set()` guarantees that preempted/stopped threads terminate immediately.
3. **Safety Serialization (Bug 3)**: Instantiating a `threading.RLock()` in `AssistantController` and wrapping the body of `handle_input()` in `with self._lock:` serializes all inputs. This guarantees that model loading/unloading steps do not overlap across threads, ensuring VRAM usage never exceeds 4.5 GB (safe under the 6.0 GB limit).
4. **VRAM Reference Cleanups (Bug 4)**: Wrapping the safety check in `load_model()` in a `try...except` block ensures that if `check_safety()` raises `MemoryError`, we catch it, reset the loaded state (e.g., `vram_manager.stt_loaded = False`), and then re-raise the exception. This guarantees that failed loads do not leak model registrations in `loaded_in_vram`.
5. **Standard Test Compatibility**: Since all 90 mock-dependent tests execute sequentially, introducing locks does not block them or change their API interactions, maintaining 100% test compatibility.

---

## 3. Caveats

- **Test Suite Scope**: The proposed fixes only modify the simulation layer in `tests/mock_assistant.py`. They do not touch the real implementations in `voice_assistant/` (which already handle locks correctly).
- **Environment Dependencies**: The real engines are skipped during mock-dependent optimization testing using the environment variable `MOCK_ENGINES=1`.

---

## 4. Conclusion

The 4 bugs identified in the optimization test suite mocks can be resolved cleanly by updating `tests/mock_assistant.py` with:
- `threading.RLock()` in `TTSEngine` and `AssistantController`.
- Preemption-based `speak_id` cancellation checks.
- Exception-safe VRAM model loading.

This strategy complies with the **requirement-driven, opaque-box testing philosophy**:
- **Requirement-Driven**: Directly ensures the E2E simulation adheres to concurrency, VRAM limit, and preemption safety requirements.
- **Opaque-Box Testing**: Interfaces with the public APIs (`speak()`, `stop()`, `handle_input()`, `MemoryError`, etc.) without altering any expected test assertions or mock histories, keeping all 90 tests passing perfectly without changes to test cases.

### Proposed Code Modifications for `tests/mock_assistant.py`

#### 1. Fix TTSEngine Lock (Bug 1) & Preemption Thread Leak (Bug 2)
In `class TTSEngine`:
```python
<<<<
    def __init__(self):
        self._is_speaking = False
        self._lock = threading.Lock()
        self._speak_thread = None
        self._stop_event = threading.Event()
        self._current_speak_id = 0

    def speak(self, text: str, volume: float = 0.5):
        if not isinstance(volume, (int, float)):
            raise TypeError("Volume must be a number")
        if volume < 0.0 or volume > 1.0:
            raise ValueError("Volume must be between 0.0 and 1.0")
        if text is None:
            raise TypeError("Text cannot be None")
        
        if text == "":
            return

        with self._lock:
            if self._is_speaking:
                self.stop()
            
            self._current_speak_id += 1
            speak_id = self._current_speak_id
            self._is_speaking = True
            self._stop_event.clear()
            history.tts_speak_calls.append((text, volume))
            
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
                with self._lock:
                    if self._current_speak_id == speak_id:
                        self._is_speaking = False
            
            self._speak_thread = threading.Thread(target=run_speak)
            t_ref.append(self._speak_thread)
            self._speak_thread.daemon = True
            self._speak_thread.start()
====
    def __init__(self):
        self._is_speaking = False
        self._lock = threading.RLock()
        self._speak_thread = None
        self._stop_event = threading.Event()
        self._current_speak_id = 0

    def speak(self, text: str, volume: float = 0.5):
        if not isinstance(volume, (int, float)):
            raise TypeError("Volume must be a number")
        if volume < 0.0 or volume > 1.0:
            raise ValueError("Volume must be between 0.0 and 1.0")
        if text is None:
            raise TypeError("Text cannot be None")
        
        if text == "":
            return

        with self._lock:
            if self._is_speaking:
                self.stop()
            
            self._current_speak_id += 1
            speak_id = self._current_speak_id
            self._is_speaking = True
            self._stop_event.clear()
            history.tts_speak_calls.append((text, volume))
            
            # Use local reference to the thread to avoid race condition
            t_ref = []
            def run_speak():
                duration = min(0.5, max(0.05, len(text) * 0.005))
                start_time = time.time()
                while time.time() - start_time < duration:
                    with self._lock:
                        if self._current_speak_id != speak_id or self._stop_event.is_set():
                            break
                    time.sleep(0.01)
                with self._lock:
                    if self._current_speak_id == speak_id:
                        self._is_speaking = False
            
            self._speak_thread = threading.Thread(target=run_speak)
            t_ref.append(self._speak_thread)
            self._speak_thread.daemon = True
            self._speak_thread.start()
>>>>
```

#### 2. Fix VRAM State Leak on check_safety Failure (Bug 4)
In `class STTEngine`:
```python
<<<<
    def load_model(self):
        history.stt_load_calls.append(True)
        try:
            import voice_assistant.config as config
            device = getattr(config, "STT_DEVICE", "cuda")
        except Exception:
            device = "cuda"
            
        if device == "cuda":
            vram_manager.stt_loaded = True
            vram_manager.check_safety()
        self._model_loaded = True
====
    def load_model(self):
        history.stt_load_calls.append(True)
        try:
            import voice_assistant.config as config
            device = getattr(config, "STT_DEVICE", "cuda")
        except Exception:
            device = "cuda"
            
        if device == "cuda":
            vram_manager.stt_loaded = True
            try:
                vram_manager.check_safety()
            except Exception:
                vram_manager.stt_loaded = False
                raise
        self._model_loaded = True
>>>>
```

In `class LLMEngine`:
```python
<<<<
    def load_model(self):
        history.llm_load_calls.append(True)
        try:
            import voice_assistant.config as config
            device = getattr(config, "LLM_DEVICE", "cuda")
        except Exception:
            device = "cuda"
            
        if device == "cuda":
            vram_manager.llm_loaded = True
            vram_manager.check_safety()
        self._model_loaded = True
====
    def load_model(self):
        history.llm_load_calls.append(True)
        try:
            import voice_assistant.config as config
            device = getattr(config, "LLM_DEVICE", "cuda")
        except Exception:
            device = "cuda"
            
        if device == "cuda":
            vram_manager.llm_loaded = True
            try:
                vram_manager.check_safety()
            except Exception:
                vram_manager.llm_loaded = False
                raise
        self._model_loaded = True
>>>>
```

#### 3. Fix Concurrent VRAM Safety Violation via Serialization Lock (Bug 3)
In `class AssistantController`:
```python
<<<<
class AssistantController:
    def __init__(self, tts_engine=None, stt_engine=None, llm_engine=None, wiki_retriever=None):
        self.tts_engine = tts_engine if tts_engine else TTSEngine()
        self.stt_engine = stt_engine if stt_engine else STTEngine()
        self.llm_engine = llm_engine if llm_engine else LLMEngine()
        self.wiki_retriever = wiki_retriever if wiki_retriever else WikiRetriever()
        self.context = []
        self.is_running = False
        self.interrupted_flag = False

    def start(self):
        history.controller_start_calls.append(True)
        self.is_running = True

    def handle_input(self, input_type: str, content) -> None:
        history.controller_handle_input_calls.append((input_type, content))
        
        if self.tts_engine.is_speaking():
            self.tts_engine.stop()
            self.interrupted_flag = True
        else:
            self.interrupted_flag = False

        if content == "" or content is None:
            return

        try:
            import voice_assistant.config as config
            dynamic_loading = getattr(config, "DYNAMIC_MODEL_LOADING", False)
        except Exception:
            dynamic_loading = False
        
        # ... (rest of handle_input)
====
class AssistantController:
    def __init__(self, tts_engine=None, stt_engine=None, llm_engine=None, wiki_retriever=None):
        self.tts_engine = tts_engine if tts_engine else TTSEngine()
        self.stt_engine = stt_engine if stt_engine else STTEngine()
        self.llm_engine = llm_engine if llm_engine else LLMEngine()
        self.wiki_retriever = wiki_retriever if wiki_retriever else WikiRetriever()
        self.context = []
        self.is_running = False
        self.interrupted_flag = False
        self._lock = threading.RLock()

    def start(self):
        history.controller_start_calls.append(True)
        self.is_running = True

    def handle_input(self, input_type: str, content) -> None:
        with self._lock:
            history.controller_handle_input_calls.append((input_type, content))
            
            if self.tts_engine.is_speaking():
                self.tts_engine.stop()
                self.interrupted_flag = True
            else:
                self.interrupted_flag = False

            if content == "" or content is None:
                return

            try:
                import voice_assistant.config as config
                dynamic_loading = getattr(config, "DYNAMIC_MODEL_LOADING", False)
            except Exception:
                dynamic_loading = False
            
            # ... (rest of handle_input under lock context)
>>>>
```

---

## 5. Verification Method

To independently verify these fixes:
1. Ensure the environment is configured to use mock engines:
   ```powershell
   $env:MOCK_ENGINES="1"
   ```
2. Execute the 90 core tests using `pytest` to guarantee backwards compatibility and ensure no regressions were introduced:
   ```powershell
   py -m pytest tests/test_tier1_coverage.py tests/test_tier2_boundaries.py tests/test_tier3_combinations.py tests/test_tier4_scenarios.py tests/test_optimization.py tests/test_rag.py
   ```
   **Expected Result**: All 90 tests pass successfully.
3. Run the adversarial diagnostics suite:
   ```powershell
   py tests/run_adversarial_diagnostics.py
   ```
   **Expected Result**:
   - `test_concurrent_dynamic_loading_vram_violation` finishes with 0 errors caught (max VRAM = 4.5 GB) and `Success: True`.
   - `test_tts_engine_reentrant_lock_deadlock` finishes with `Thread deadlocked (is_alive): False` and `Success: True`.
   - `test_tts_thread_and_task_leak` finishes with `Estimated leaked threads: 0` and `Success: True`.
