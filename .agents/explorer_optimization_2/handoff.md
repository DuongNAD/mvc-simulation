# Handoff Report: R6 Hardware Optimization E2E Test Suite Design

## 1. Observation
From analyzing the codebase, we observe the following:

- **E2E Mock and Environment Patching**: In `tests/mock_assistant.py`, the system intercepts imports of the `voice_assistant` package when `MOCK_ENGINES=1` is set:
  ```python
  288: should_mock = mock_engines_env or not voice_assistant_exists
  289: 
  290: if should_mock:
  291:     va = ModuleType("voice_assistant")
  292:     sys.modules["voice_assistant"] = va
  ...
  ```
  This overrides the real classes with custom mock wrappers for testing purposes.
- **Existing Engine Mock Limits**: Currently, `tests/mock_assistant.py` implements mock versions of `STTEngine`, `LLMEngine`, `TTSEngine`, and `AssistantController`, but they lack methods for `load_model()` and `unload_model()`, device configurations, or dynamic loading sequencing checks.
- **Test Discovery**: `tests/run_tests.py` discovers tests matching `test_tier*.py` and `test_rag.py`:
  ```python
  33:     # Discover all tests matching both 'test_tier*.py' and 'test_rag.py'
  34:     loader = unittest.TestLoader()
  35:     suite_tier = loader.discover(start_dir=tests_dir, pattern="test_tier*.py")
  36:     suite_rag = loader.discover(start_dir=tests_dir, pattern="test_rag.py")
  37:     suite = unittest.TestSuite([suite_tier, suite_rag])
  ```
- **Test Coverage**: Currently, there are 75 passing test cases across the five core suites and the RAG validation suite. This is confirmed by running `py tests/run_tests.py`:
  ```
  Ran 75 tests in 0.403s
  OK
  ```
- **Interface Contracts**: According to `e:\test\mvc-simulation\.agents\sub_orch_testing_gen1\SCOPE.md`, the contracts for optimization include:
  - `STTEngine`: `load_model() -> None`, `unload_model() -> None`, and CPU offloading.
  - `LLMEngine`: `load_model() -> None`, `unload_model() -> None`.
  - `AssistantController`: Dynamic model loading schedule ensuring STT and LLM models are not loaded in VRAM concurrently if `DYNAMIC_MODEL_LOADING` is enabled.

---

## 2. Logic Chain
To implement the R6 Hardware Optimization E2E tests cleanly without breaking existing tests, we propose a step-by-step modification strategy:

1. **Configurations**: We will add the following device variables to the mocked `voice_assistant.config` in `tests/mock_assistant.py`:
   - `DYNAMIC_MODEL_LOADING` (default: `False` to maintain compatibility with existing tests).
   - `STT_DEVICE` (default: `"cuda"`).
   - `LLM_DEVICE` (default: `"cuda"`).
   - `TTS_DEVICE` (default: `"cpu"`).

2. **Model Load Tracking and VRAM Safety**:
   - Introduce a module-level dictionary in `tests/mock_assistant.py`, `loaded_engines = {}`, mapping engine names (`"stt"`, `"llm"`) to their active devices.
   - For `STTEngine` and `LLMEngine`, implement `load_model()` and `unload_model()`.
   - In `load_model()`, check if `DYNAMIC_MODEL_LOADING` is `True` and `device == "cuda"`. If the other engine is already loaded on `"cuda"`, raise a `RuntimeError("VRAM safety violation")`.
   - Update `MockHistory` to record `stt_load_calls`, `stt_unload_calls`, `llm_load_calls`, and `llm_unload_calls`.

3. **Backward Compatibility**:
   - In `STTEngine.__init__` and `LLMEngine.__init__`, if `DYNAMIC_MODEL_LOADING` is `False`, we will call `load_model()` inside `__init__`. This ensures existing tests that instantiate these engines directly can still call `transcribe()` and `generate_response()` immediately without manual setup.

4. **Controller Dynamic Orchestration**:
   - Modify `AssistantController.handle_input()` to check if `DYNAMIC_MODEL_LOADING` is `True`.
   - If enabled, wrap `transcribe()` in `load_model()` / `unload_model()` and `generate_response()` in `load_model()` / `unload_model()`, using `try...finally` structures to guarantee cleanup in case of exceptions.

5. **Test Discovery Expansion**:
   - Modify `tests/run_tests.py` to also discover `test_optimization.py` and merge it into the running suite.

---

## 3. Caveats
- **Mock Environment Constraint**: Since `MOCK_ENGINES=1` is injected during testing, the E2E verification validates the *orchestration and routing logic* of the configurations and safety checks. The production behavior of faster-whisper and transformers under these states will need separate unit tests on hardware-equipped machines, which is out of scope for these mocked E2E tests.
- **Hardware Agnostic**: Tests are designed to run safely on any machine (even those without CUDA GPUs) because all hardware VRAM boundaries are mocked and simulated, requiring no external libraries or paid APIs.

---

## 4. Conclusion & Proposed Implementation
The worker should implement the changes outlined in the diffs and files below.

### 4.1 Changes to `tests/mock_assistant.py`
Add tracking, load/unload logic, device configurations, and update the controller:

```python
# In MockHistory
class MockHistory:
    def __init__(self):
        self.tts_speak_calls = []
        self.tts_stop_calls = []
        self.stt_transcribe_calls = []
        self.llm_generate_calls = []
        self.controller_handle_input_calls = []
        self.controller_start_calls = []
        self.wiki_retrieve_calls = []
        # R6 Optimization calls
        self.stt_load_calls = []
        self.stt_unload_calls = []
        self.llm_load_calls = []
        self.llm_unload_calls = []

# Module-level variable for tracking loaded models
loaded_engines = {}

def reset_history():
    history.tts_speak_calls.clear()
    history.tts_stop_calls.clear()
    history.stt_transcribe_calls.clear()
    history.llm_generate_calls.clear()
    history.controller_handle_input_calls.clear()
    history.controller_start_calls.clear()
    history.wiki_retrieve_calls.clear()
    # R6 resets
    history.stt_load_calls.clear()
    history.stt_unload_calls.clear()
    history.llm_load_calls.clear()
    history.llm_unload_calls.clear()
    loaded_engines.clear()

# STTEngine load/unload
class STTEngine:
    def __init__(self, model_size: str = "base"):
        self.transcriptions = {}
        self.default_transcription = "Simulated speech transcription"
        import voice_assistant.config as config
        self.device = getattr(config, "STT_DEVICE", "cuda")
        self.model_loaded = False
        if not getattr(config, "DYNAMIC_MODEL_LOADING", False):
            self.load_model()

    def load_model(self) -> None:
        import voice_assistant.config as config
        history.stt_load_calls.append(self.device)
        if getattr(config, "DYNAMIC_MODEL_LOADING", False) and self.device == "cuda":
            if loaded_engines.get("llm") == "cuda":
                raise RuntimeError("VRAM safety violation: STT and LLM models loaded in VRAM concurrently")
        self.model_loaded = True
        loaded_engines["stt"] = self.device

    def unload_model(self) -> None:
        history.stt_unload_calls.append(True)
        self.model_loaded = False
        loaded_engines.pop("stt", None)

    def transcribe(self, audio_path_or_data) -> str:
        if not self.model_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        # [Existing transcribe content...]

# LLMEngine load/unload
class LLMEngine:
    def __init__(self):
        self.responses = {}
        self.default_response = "Simulated assistant response"
        self.simulate_offline = False
        import voice_assistant.config as config
        self.device = getattr(config, "LLM_DEVICE", "cuda")
        self.model_loaded = False
        if not getattr(config, "DYNAMIC_MODEL_LOADING", False):
            self.load_model()

    def load_model(self) -> None:
        import voice_assistant.config as config
        history.llm_load_calls.append(self.device)
        if getattr(config, "DYNAMIC_MODEL_LOADING", False) and self.device == "cuda":
            if loaded_engines.get("stt") == "cuda":
                raise RuntimeError("VRAM safety violation: STT and LLM models loaded in VRAM concurrently")
        self.model_loaded = True
        loaded_engines["llm"] = self.device

    def unload_model(self) -> None:
        history.llm_unload_calls.append(True)
        self.model_loaded = False
        loaded_engines.pop("llm", None)

    def generate_response(self, prompt: str, context: list = None, retrieval_context: str = "") -> str:
        if not self.model_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        # [Existing generate_response content...]

# In sys.modules overrides for voice_assistant.config
    va_config = ModuleType("voice_assistant.config")
    va_config.DEFAULT_VOLUME = 0.5
    va_config.OFFLINE_MODE = True
    va_config.DEVICE = "cuda"
    # New configurations
    va_config.DYNAMIC_MODEL_LOADING = False
    va_config.STT_DEVICE = "cuda"
    va_config.LLM_DEVICE = "cuda"
    va_config.TTS_DEVICE = "cpu"
    sys.modules["voice_assistant.config"] = va_config
    va.config = va_config

# AssistantController sequential orchestration
class AssistantController:
    # [Existing init...]

    def handle_input(self, input_type: str, content) -> None:
        import voice_assistant.config as config
        history.controller_handle_input_calls.append((input_type, content))
        
        if self.tts_engine.is_speaking():
            self.tts_engine.stop()
            self.interrupted_flag = True
        else:
            self.interrupted_flag = False

        if content == "" or content is None:
            return

        prompt = None
        if input_type in ("voice", "audio"):
            if getattr(config, "DYNAMIC_MODEL_LOADING", False):
                self.stt_engine.load_model()
            try:
                prompt = self.stt_engine.transcribe(content)
            finally:
                if getattr(config, "DYNAMIC_MODEL_LOADING", False):
                    self.stt_engine.unload_model()
        elif input_type == "text":
            prompt = content
          
        # [Existing retrieval chunk logic...]

        if getattr(config, "DYNAMIC_MODEL_LOADING", False):
            self.llm_engine.load_model()
        try:
            response = self.llm_engine.generate_response(prompt, self.context, retrieval_context=retrieval_context)
        finally:
            if getattr(config, "DYNAMIC_MODEL_LOADING", False):
                self.llm_engine.unload_model()
        
        # [Existing context update & speak call...]
```

### 4.2 New File: `tests/test_optimization.py`
Create this new verification suite:

```python
import os
import sys
import unittest
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tests.mock_assistant as mock_assistant
from voice_assistant.tts import TTSEngine
from voice_assistant.stt import STTEngine
from voice_assistant.llm import LLMEngine
from voice_assistant.controller import AssistantController
import voice_assistant.config as config

class TestHardwareOptimization(unittest.TestCase):
    def setUp(self):
        mock_assistant.reset_history()
        config.DYNAMIC_MODEL_LOADING = False
        config.STT_DEVICE = "cuda"
        config.LLM_DEVICE = "cuda"
        config.TTS_DEVICE = "cpu"

    def tearDown(self):
        mock_assistant.reset_history()

    # ==========================================
    # Tier 1: Happy-Path Coverage (5 cases)
    # ==========================================
    def test_stt_model_load_unload(self):
        config.DYNAMIC_MODEL_LOADING = True
        engine = STTEngine()
        self.assertFalse(engine.model_loaded)
        
        engine.load_model()
        self.assertTrue(engine.model_loaded)
        self.assertEqual(len(mock_assistant.history.stt_load_calls), 1)
        
        engine.unload_model()
        self.assertFalse(engine.model_loaded)
        self.assertEqual(len(mock_assistant.history.stt_unload_calls), 1)

    def test_llm_model_load_unload(self):
        config.DYNAMIC_MODEL_LOADING = True
        engine = LLMEngine()
        self.assertFalse(engine.model_loaded)
        
        engine.load_model()
        self.assertTrue(engine.model_loaded)
        self.assertEqual(len(mock_assistant.history.llm_load_calls), 1)
        
        engine.unload_model()
        self.assertFalse(engine.model_loaded)
        self.assertEqual(len(mock_assistant.history.llm_unload_calls), 1)

    def test_stt_cpu_device_configuration(self):
        config.STT_DEVICE = "cpu"
        engine = STTEngine()
        self.assertEqual(engine.device, "cpu")
        self.assertTrue(engine.model_loaded) # Auto-loaded because DYNAMIC_MODEL_LOADING = False

    def test_tts_cpu_device_configuration(self):
        config.TTS_DEVICE = "cpu"
        engine = TTSEngine()
        self.assertEqual(engine.device, "cpu")

    def test_dynamic_model_loading_sequence(self):
        config.DYNAMIC_MODEL_LOADING = True
        controller = AssistantController()
        controller.handle_input("voice", "test_query.wav")
        
        # Verify STT model loaded then unloaded
        self.assertEqual(len(mock_assistant.history.stt_load_calls), 1)
        self.assertEqual(len(mock_assistant.history.stt_unload_calls), 1)
        
        # Verify LLM model loaded then unloaded
        self.assertEqual(len(mock_assistant.history.llm_load_calls), 1)
        self.assertEqual(len(mock_assistant.history.llm_unload_calls), 1)

    # ==========================================
    # Tier 2: Boundary & Edge Cases (5 cases)
    # ==========================================
    def test_transcribe_without_load_error(self):
        config.DYNAMIC_MODEL_LOADING = True
        engine = STTEngine()
        with self.assertRaises(RuntimeError):
            engine.transcribe("sample.wav")

    def test_generate_response_without_load_error(self):
        config.DYNAMIC_MODEL_LOADING = True
        engine = LLMEngine()
        with self.assertRaises(RuntimeError):
            engine.generate_response("hello", [])

    def test_consecutive_loads_and_unloads(self):
        config.DYNAMIC_MODEL_LOADING = True
        engine = STTEngine()
        engine.load_model()
        engine.load_model() # Should not raise
        self.assertTrue(engine.model_loaded)
        
        engine.unload_model()
        engine.unload_model() # Should not raise
        self.assertFalse(engine.model_loaded)

    def test_vram_concurrent_load_violation(self):
        config.DYNAMIC_MODEL_LOADING = True
        stt = STTEngine()
        llm = LLMEngine()
        
        stt.load_model()
        with self.assertRaises(RuntimeError):
            llm.load_model()

    def test_invalid_device_configuration(self):
        config.STT_DEVICE = "tpu"
        engine = STTEngine()
        self.assertEqual(engine.device, "tpu")

    # ==========================================
    # Tier 3: Cross-Feature Combinations (3 cases)
    # ==========================================
    def test_cpu_offloading_bypasses_vram_safety(self):
        config.DYNAMIC_MODEL_LOADING = True
        config.STT_DEVICE = "cpu"
        config.LLM_DEVICE = "cuda"
        
        stt = STTEngine()
        llm = LLMEngine()
        
        # CPU loading does not conflict with CUDA VRAM safety rules
        stt.load_model()
        llm.load_model()
        self.assertTrue(stt.model_loaded)
        self.assertTrue(llm.model_loaded)

    def test_controller_error_recovery_unloads(self):
        config.DYNAMIC_MODEL_LOADING = True
        controller = AssistantController()
        # Trigger an error during transcribe
        controller.stt_engine.transcriptions["broken.wav"] = None # Will cause TypeError
        
        with self.assertRaises(TypeError):
            controller.handle_input("voice", "broken.wav")
            
        # Ensure STT model was unloaded despite error
        self.assertEqual(len(mock_assistant.history.stt_unload_calls), 1)

    def test_volume_change_with_cpu_tts(self):
        config.TTS_DEVICE = "cpu"
        controller = AssistantController()
        config.DEFAULT_VOLUME = 0.75
        controller.handle_input("text", "Hello assistant")
        self.assertEqual(mock_assistant.history.tts_speak_calls[0][1], 0.75)

    # ==========================================
    # Tier 4: Real-World Scenarios (2 cases)
    # ==========================================
    def test_scenario_dynamic_loading_low_vram(self):
        """Scenario: User chats on low-VRAM system, ensuring sequential load/unload"""
        config.DYNAMIC_MODEL_LOADING = True
        config.STT_DEVICE = "cuda"
        config.LLM_DEVICE = "cuda"
        
        controller = AssistantController()
        controller.handle_input("voice", "query1.wav")
        
        self.assertEqual(len(mock_assistant.history.stt_load_calls), 1)
        self.assertEqual(len(mock_assistant.history.stt_unload_calls), 1)
        self.assertEqual(len(mock_assistant.history.llm_load_calls), 1)
        self.assertEqual(len(mock_assistant.history.llm_unload_calls), 1)
        
        # Verify they were never active at the same time
        self.assertEqual(len(mock_assistant.loaded_engines), 0)

    def test_scenario_stt_cpu_offloaded_continuous_chat(self):
        """Scenario: STT offloaded to CPU, LLM on CUDA. Checks no VRAM overlap issues"""
        config.DYNAMIC_MODEL_LOADING = True
        config.STT_DEVICE = "cpu"
        config.LLM_DEVICE = "cuda"
        
        controller = AssistantController()
        controller.handle_input("voice", "query2.wav")
        
        self.assertEqual(len(mock_assistant.history.stt_load_calls), 1)
        self.assertEqual(len(mock_assistant.history.llm_load_calls), 1)
```

### 4.3 Changes to `tests/run_tests.py`
Modify `run_tests.py` to add discovery for `test_optimization.py`:

```python
    # Discover all tests matching both 'test_tier*.py', 'test_rag.py', and 'test_optimization.py'
    loader = unittest.TestLoader()
    suite_tier = loader.discover(start_dir=tests_dir, pattern="test_tier*.py")
    suite_rag = loader.discover(start_dir=tests_dir, pattern="test_rag.py")
    suite_opt = loader.discover(start_dir=tests_dir, pattern="test_optimization.py")
    suite = unittest.TestSuite([suite_tier, suite_rag, suite_opt])
```

### 4.4 Documentation Revisions
1. **`TEST_INFRA.md` at root**: Add a new sub-section under "Feature Inventory" details for R6 Hardware Optimization, list `tests/test_optimization.py` under the "Test Files" section, and update the coverage thresholds table:
   - Target Total: **90 cases**.
2. **`TEST_READY.md` at root**: Provide a plan for the worker to run the test suite and replace the execution log in `TEST_READY.md` with the new log output containing all 90 successful tests.

---

## 5. Verification Method
1. **Test Execution Command**:
   - `py tests/run_tests.py`
2. **Success Metrics**:
   - Clean exit code `0`.
   - Output lists `Total Tests Run: 90` with `Passed: 90`, `Failed: 0`, and `Errors: 0`.
3. **Invalidation Conditions**:
   - Total test run count is less than 90.
   - Any runtime exceptions or failures when executing `test_optimization.py` or existing suites.
   - Regression in existing 75 test cases due to missing model load states.
