# R6 Hardware Optimization Test Suite Design and Handoff Report

This report outlines the observations, logical reasoning, proposed implementation details, and verification methods for integrating the new **R6 Hardware Optimization** feature into the Interactive Voice Assistant's E2E test suite.

---

## 1. Observation

During the read-only exploration of the workspace `e:\test\mvc-simulation`, the following files and behaviors were examined:

### 1.1 Current Mock System (`tests/mock_assistant.py`)
- The mock suite simulates `voice_assistant` submodules (`config`, `tts`, `stt`, `llm`, `wiki`, `controller`, `main`) by injecting custom mocks into `sys.modules` when the environment variable `MOCK_ENGINES=1` is active.
- `STTEngine` (lines 89–115) does not currently implement `load_model()`, `unload_model()`, or VRAM simulation. Its `transcribe()` method directly returns transcriptions without checking model state.
- `LLMEngine` (lines 117–153) does not implement `load_model()`, `unload_model()`, or VRAM simulation. Its `generate_response()` runs regardless of whether the model has been initialized or loaded in VRAM.
- `AssistantController` (lines 185–241) does not orchestrate loading/unloading sequences for STT and LLM models. It calls `self.stt_engine.transcribe()` and `self.llm_engine.generate_response()` sequentially without scheduling VRAM resources.
- `MockHistory` (lines 8–28) tracks TTS calls, STT transcribe calls, LLM generate calls, and controller calls, but does not track model loading/unloading event histories.

### 1.2 Current Test Runner (`tests/run_tests.py`)
- The runner discovers tests matching `test_tier*.py` and `test_rag.py` (lines 33–37) under `tests/`.
- It executes discovered tests and summarizes counts. Running the runner yields the following baseline output:
  ```
  Ran 75 tests in 0.599s
  OK
  Total Tests Run: 75
  Passed:           75
  Failed:           0
  Errors:           0
  RESULT: PASS
  ```

### 1.3 Target Contracts & Requirements
- `STTEngine` and `LLMEngine` must support `load_model()` and `unload_model()`.
- `STTEngine` must support CPU offloading (`STT_DEVICE` device configuration).
- `TTSEngine` must support CPU execution (`TTS_DEVICE`).
- `AssistantController` must orchestrate dynamic loading schedules so that STT and LLM are not in VRAM concurrently if `DYNAMIC_MODEL_LOADING` is enabled.
- VRAM safety rules must be enforced based on simulated VRAM consumption.

---

## 2. Logic Chain

To test the R6 Hardware Optimization features under the requirement-driven, opaque-box, and offline-safe philosophy, we must design changes to the mock assistant and a new test file `tests/test_optimization.py`.

### 2.1 Update Strategy for `tests/mock_assistant.py`

#### A. Expand `MockHistory` and `reset_history`
We will track engine load/unload history to assert correct order of execution:
```python
# In MockHistory
self.stt_load_calls = []
self.stt_unload_calls = []
self.llm_load_calls = []
self.llm_unload_calls = []

# In reset_history()
history.stt_load_calls.clear()
history.stt_unload_calls.clear()
history.llm_load_calls.clear()
history.llm_unload_calls.clear()
```

#### B. Introduce `MockVRAMManager`
We need a simulated VRAM manager that tracks current loaded engines, checks device configurations, and throws `MemoryError` if the VRAM limit is exceeded:
```python
class MockVRAMManager:
    def __init__(self):
        self.vram_limit = 6.0       # GB
        self.stt_usage = 2.0        # GB
        self.llm_usage = 4.5        # GB
        self.stt_loaded = False
        self.llm_loaded = False

    def get_current_vram(self) -> float:
        vram = 0.0
        import voice_assistant.config as config
        stt_device = getattr(config, "STT_DEVICE", "cuda")
        llm_device = getattr(config, "LLM_DEVICE", "cuda")
        
        if self.stt_loaded and stt_device == "cuda":
            vram += self.stt_usage
        if self.llm_loaded and llm_device == "cuda":
            vram += self.llm_usage
        return vram

    def check_safety(self) -> None:
        current = self.get_current_vram()
        if current > self.vram_limit:
            raise MemoryError(f"Out of VRAM: Current VRAM usage {current}GB exceeds limit {self.vram_limit}GB")

    def reset(self):
        self.stt_loaded = False
        self.llm_loaded = False

vram_manager = MockVRAMManager()
```

#### C. Update `STTEngine` Mock
```python
class STTEngine:
    def __init__(self):
        self.transcriptions = {}
        self.default_transcription = "Simulated speech transcription"
        self.model_loaded = False

    def load_model(self) -> None:
        history.stt_load_calls.append(True)
        self.model_loaded = True
        vram_manager.stt_loaded = True
        vram_manager.check_safety()

    def unload_model(self) -> None:
        history.stt_unload_calls.append(True)
        self.model_loaded = False
        vram_manager.stt_loaded = False

    def transcribe(self, audio_path_or_data) -> str:
        import voice_assistant.config as config
        dynamic_loading = getattr(config, "DYNAMIC_MODEL_LOADING", False)
        if dynamic_loading and not self.model_loaded:
            raise RuntimeError("STT model must be loaded before transcribing when dynamic model loading is enabled")
        
        # Existing transcription logic follows...
```

#### D. Update `LLMEngine` Mock
```python
class LLMEngine:
    def __init__(self):
        self.responses = {}
        self.default_response = "Simulated assistant response"
        self.simulate_offline = False
        self.model_loaded = False

    def load_model(self) -> None:
        history.llm_load_calls.append(True)
        self.model_loaded = True
        vram_manager.llm_loaded = True
        vram_manager.check_safety()

    def unload_model(self) -> None:
        history.llm_unload_calls.append(True)
        self.model_loaded = False
        vram_manager.llm_loaded = False

    def generate_response(self, prompt: str, context: list = None, retrieval_context: str = "") -> str:
        import voice_assistant.config as config
        dynamic_loading = getattr(config, "DYNAMIC_MODEL_LOADING", False)
        if dynamic_loading and not self.model_loaded:
            raise RuntimeError("LLM model must be loaded before generating response when dynamic model loading is enabled")
            
        # Existing response generation logic follows...
```

#### E. Update `AssistantController` Mock
The scheduler needs to orchestrate load/unload sequences.
```python
    def handle_input(self, input_type: str, content) -> None:
        history.controller_handle_input_calls.append((input_type, content))
        
        if self.tts_engine.is_speaking():
            self.tts_engine.stop()
            self.interrupted_flag = True
        else:
            self.interrupted_flag = False

        if content == "" or content is None:
            return

        import voice_assistant.config as config
        dynamic_loading = getattr(config, "DYNAMIC_MODEL_LOADING", False)

        if input_type in ("voice", "audio"):
            if dynamic_loading:
                # Dynamic load schedule: Unload LLM if loaded, then load STT
                if getattr(self.llm_engine, "model_loaded", False):
                    self.llm_engine.unload_model()
                self.stt_engine.load_model()
            
            try:
                prompt = self.stt_engine.transcribe(content)
            finally:
                if dynamic_loading:
                    # Unload STT after transcribe
                    self.stt_engine.unload_model()
        elif input_type == "text":
            prompt = content
        else:
            raise ValueError(f"Invalid input type: {input_type}")

        if not prompt:
            return

        retrieval_context = ""
        try:
            chunks = self.wiki_retriever.retrieve(prompt)
            retrieval_context = "\n".join(chunks)
        except Exception:
            retrieval_context = ""

        if dynamic_loading:
            # Load LLM for generation
            self.llm_engine.load_model()

        try:
            response = self.llm_engine.generate_response(prompt, self.context, retrieval_context=retrieval_context)
        except Exception as e:
            raise e

        self.context.append({"role": "user", "content": prompt})
        self.context.append({"role": "assistant", "content": response})

        volume = 0.5
        try:
            volume = config.DEFAULT_VOLUME
        except Exception:
            pass
            
        self.tts_engine.speak(response, volume=volume)
```

#### F. Update Mock Config
In `mock_assistant.py` module setup (lines 290–330), define new default variables:
```python
    va_config.DYNAMIC_MODEL_LOADING = False
    va_config.STT_DEVICE = "cuda"
    va_config.LLM_DEVICE = "cuda"
    va_config.TTS_DEVICE = "cpu"
```

---

### 2.2 Proposed Test Suite (`tests/test_optimization.py`)

A new test suite consisting of **exactly 15 tests** covering Tiers 1-4 should be implemented:

#### Tier 1: Happy Paths (5 cases)
1. `test_stt_model_load_unload`: Verifies that STTEngine `load_model()` and `unload_model()` work correctly, updating internal state and recording mock history.
2. `test_llm_model_load_unload`: Verifies that LLMEngine `load_model()` and `unload_model()` work correctly, updating internal state and recording mock history.
3. `test_stt_device_configuration`: Verifies that the STT engine accepts device settings (e.g. CPU or CUDA) through `config.STT_DEVICE` and registers them properly.
4. `test_tts_device_configuration`: Verifies that the TTS engine accepts device configurations through `config.TTS_DEVICE` and operates without errors.
5. `test_controller_optimization_happy_path`: Verifies that the controller processes a voice query with `DYNAMIC_MODEL_LOADING=True` by loading/unloading STT and LLM models sequentially without overlapping in VRAM.

#### Tier 2: Boundary & Edge Cases (5 cases)
6. `test_stt_transcribe_without_load_raises_error`: Verifies that if `DYNAMIC_MODEL_LOADING` is enabled, calling `transcribe()` on `STTEngine` without first loading the model raises a `RuntimeError`.
7. `test_llm_generate_without_load_raises_error`: Verifies that if `DYNAMIC_MODEL_LOADING` is enabled, calling `generate_response()` on `LLMEngine` without first loading the model raises a `RuntimeError`.
8. `test_double_load_and_unload_robustness`: Verifies that calling `load_model()` on an already loaded engine or `unload_model()` on an already unloaded engine is handled gracefully without errors.
9. `test_vram_limit_exceeded_error`: Verifies that if `DYNAMIC_MODEL_LOADING` is False and both engines run on CUDA/GPU, attempting to load both models concurrently exceeds the 6.0 GB VRAM limit and throws a `MemoryError`.
10. `test_dynamic_loading_toggle_during_run`: Verifies that switching `config.DYNAMIC_MODEL_LOADING` dynamically between requests correctly updates controller orchestration logic on the fly.

#### Tier 3: Cross-Feature Combinations (3 cases)
11. `test_cpu_offloading_prevents_vram_overflow`: Verifies that if `DYNAMIC_MODEL_LOADING` is False, but STT is configured on CPU (`STT_DEVICE="cpu"`), both models can be loaded concurrently without raising a `MemoryError` (since STT uses 0 VRAM).
12. `test_consecutive_voice_and_text_requests`: Verifies a sequence of voice and text inputs under dynamic loading, ensuring that the controller correctly loads/unloads models to minimize VRAM usage while avoiding redundant loads for text-only inputs.
13. `test_model_unloading_on_controller_failure`: Verifies that if transcription or LLM generation fails (raises an exception), the controller catches it and still safely unloads the currently active model (STT/LLM) via `finally` blocks, preventing VRAM leaks.

#### Tier 4: Real-World Scenarios (2 cases)
14. `test_scenario_vram_constrained_voice_chat`:
    - *Scenario*: User has a low-VRAM GPU (6.0 GB limit) and conducts a voice chat with dynamic model loading enabled.
    - *Verification*: Evaluates a full multi-turn voice exchange. Asserts that STT and LLM models are never loaded concurrently on GPU, total VRAM usage never exceeds the 6.0 GB threshold, and speech outputs occur correctly.
15. `test_scenario_cpu_offloaded_fast_voice_chat`:
    - *Scenario*: User offloads STT to CPU (`STT_DEVICE="cpu"`) and keeps LLM on GPU (`LLM_DEVICE="cuda"`) with `DYNAMIC_MODEL_LOADING=False` to maximize speed and bypass load latency.
    - *Verification*: Evaluates multi-turn chat. Confirms that no load/unload actions are triggered on every turn, but total GPU VRAM stays within the 6.0 GB limit (only 4.5 GB LLM on GPU), ensuring high-speed safe execution.

---

### 2.3 Proposed Changes to `tests/run_tests.py`

Update `tests/run_tests.py` to discover and run `test_optimization.py`:
```python
    # Discover all tests matching 'test_tier*.py', 'test_rag.py', and 'test_optimization.py'
    loader = unittest.TestLoader()
    suite_tier = loader.discover(start_dir=tests_dir, pattern="test_tier*.py")
    suite_rag = loader.discover(start_dir=tests_dir, pattern="test_rag.py")
    suite_opt = loader.discover(start_dir=tests_dir, pattern="test_optimization.py")
    suite = unittest.TestSuite([suite_tier, suite_rag, suite_opt])
```

---

### 2.4 Plan for `TEST_READY.md` & `TEST_INFRA.md`

1. **TEST_INFRA.md**:
   - Update **Section 1 (Test Philosophy)** to cover VRAM constraints and hardware offloading validation.
   - Update **Section 2 (Feature Inventory)** to add a 7th category: "Hardware Optimization & VRAM Management".
   - Update **Section 3.2 (Test Files)** to list `tests/test_optimization.py`.
   - Update **Section 4 (Real-World Application Scenarios)** to append:
     - *Scenario 8: VRAM-Constrained Voice Chat (Dynamic Loading)*
     - *Scenario 9: CPU-Offloaded Fast Voice Chat (No Dynamic Latency)*
   - Update **Section 5 (Coverage Thresholds)** to increase the test numbers (Tier 1: 35 cases, Tier 2: 35 cases, Tier 3: 11 cases, Tier 4: 9 cases, Total: 90 cases).

2. **TEST_READY.md**:
   - Update **Test Summary** and **Execution Counts** to state: **90 test cases** (60 original + 15 RAG + 15 optimization tests).
   - Update the execution log output sample to display optimization test cases passing.

---

## 3. Caveats

- **Simulation Bounds**: The VRAM consumption is simulated (LLM = 4.5 GB, STT = 2.0 GB, Limit = 6.0 GB). These values are for verification of logic under constrained environments.
- **Offline Context**: All tests run locally using mocks, preserving the offline verification safety rule. No external libraries/drivers (like actual CUDA runtimes) are required since hardware state is simulated in the mock engines.
- **TTS Device Configuration**: The default Windows SAPI5 / PowerShell backend runs on the CPU. The configuration `TTS_DEVICE` is tracked and verified for contract compliance, but does not change underlying execution since SAPI5 is natively a CPU-bound process.

---

## 4. Conclusion

The proposed E2E test plan successfully addresses the new R6 Hardware Optimization requirement by extending `tests/mock_assistant.py` and designing a comprehensive 15-test suite in `tests/test_optimization.py`. This design preserves the requirement-driven, opaque-box, and offline-safe testing philosophy.

---

## 5. Verification Method

To verify the implementation:
1. **Command**: Run `py tests/run_tests.py` in the project root directory.
2. **Success Criterion**: The runner must output a `RESULT: PASS` with 90 tests executed (90 passed, 0 failed, 0 errors).
3. **Verify files**: Inspect `TEST_INFRA.md`, `tests/mock_assistant.py`, `tests/test_optimization.py`, and `TEST_READY.md`.
