# Handoff Report: R6 Hardware Optimization Verification Plan

## 1. Observations
An analysis of the current test suite, config files, and mocks shows:
- **Mock Sys.Modules Injection**: E2E test runs patch the `voice_assistant` package modules using dynamic injection in `tests/mock_assistant.py` (lines 290-329) when `MOCK_ENGINES=1` is set.
- **Engines Setup**: The current `STTEngine` and `LLMEngine` implementations in `voice_assistant/stt.py` and `voice_assistant/llm.py` load models during class construction and lack the `load_model()` and `unload_model()` methods.
- **Config file**: The existing configuration file `voice_assistant/config.py` does not contain variables for `DYNAMIC_MODEL_LOADING`, `STT_DEVICE`, `LLM_DEVICE`, or `TTS_DEVICE`.
- **Test Discovery**: `tests/run_tests.py` uses `unittest.TestLoader().discover` to scan for files matching `test_tier*.py` and `test_rag.py` (lines 33-37), executing 75 test cases in total.
- **Test Attestation**: `TEST_READY.md` lists 75 successful test cases spanning Tiers 1-4 and RAG verification.

---

## 2. Logic Chain
To support and verify the R6 Hardware Optimization features under the E2E suite, we propose:
1. **Extend `voice_assistant/config.py`**: Add new configuration parameters with default values representing baseline execution (`DYNAMIC_MODEL_LOADING = False`, etc.).
2. **Update `tests/mock_assistant.py`**:
   - Introduce a module-level `loaded_in_vram = set()` to dynamically track which engines are loaded in CUDA VRAM.
   - Update `MockHistory` and `reset_history()` to clear and track engine load/unload calls.
   - Add `load_model()` and `unload_model()` methods to mock `STTEngine` and `LLMEngine`. If `device == "cuda"`, `load_model()` registers the engine in `loaded_in_vram`.
   - Enforce VRAM Safety: If `DYNAMIC_MODEL_LOADING` is enabled, check if another engine is in `loaded_in_vram`. If a violation occurs, raise `RuntimeError("VRAM Overflow...")`.
   - Enforce execution safety: `transcribe` and `generate_response` should verify that the model is loaded when `DYNAMIC_MODEL_LOADING` is enabled.
   - Ensure backward compatibility: When `DYNAMIC_MODEL_LOADING` is `False`, set `_is_model_loaded = True` by default in constructors so that existing 75 test cases continue to run successfully.
   - Update `AssistantController.handle_input` to execute the sequential load -> run -> unload flow for STT and LLM when dynamic loading is enabled.
3. **Design `tests/test_optimization.py`**: Create 14 test cases spanning Tiers 1-4 targeting happy path loading/unloading, boundary conditions (such as running unloaded engines or simulating concurrent CUDA load failures), and real-world workflows (such as low-VRAM conversational turn-taking).
4. **Update `tests/run_tests.py`**: Add `test_optimization.py` discovery pattern to run the new suite, increasing total test cases to 89.
5. **Revise Documentation**: Document features in `TEST_INFRA.md` and outline the final attestation changes for `TEST_READY.md`.

---

## 3. Caveats
- Real hardware engines (Faster-Whisper and Qwen-7B-Instruct) are modeled through the mock assistant for test execution speed and offline-safety. The actual source code files will need to expose matching `load_model()` and `unload_model()` interfaces as part of the backend integration.
- Hardware constraints are mock-simulated without calling PyTorch CUDA APIs directly, preventing requirements for expensive GPUs or external APIs during E2E verification.

---

## 4. Conclusion
The proposed plan will verify the new R6 Hardware Optimization features and VRAM safety rules using requirement-driven, opaque-box E2E testing without breaking existing functionality. Total test counts will successfully increase from 75 to 89 tests.

---

## 5. Verification Method
1. Execute the test suite via the test runner:
   ```powershell
   python tests/run_tests.py
   ```
2. Verify output summary shows:
   - `Total Tests Run: 89`
   - `Passed: 89`
   - `RESULT: PASS`

---

## 6. Remaining Work (Concrete Next Steps for the Worker)

### Step 1: Update config file
Add the following configuration settings to `voice_assistant/config.py`:
```python
# Hardware Optimization Configuration
DYNAMIC_MODEL_LOADING = False  # Set to True to enable sequential model loading
STT_DEVICE = "cuda"            # "cuda" or "cpu"
LLM_DEVICE = "cuda"            # "cuda" or "cpu"
TTS_DEVICE = "cpu"             # "cpu"
```

### Step 2: Implement updates in `tests/mock_assistant.py`

#### A. Update Call History Tracking
Modify lines 8 to 28 of `tests/mock_assistant.py` as follows:
```python
# Call history tracker to audit E2E test flows
class MockHistory:
    def __init__(self):
        self.tts_speak_calls = []
        self.tts_stop_calls = []
        self.stt_transcribe_calls = []
        self.llm_generate_calls = []
        self.controller_handle_input_calls = []
        self.controller_start_calls = []
        self.wiki_retrieve_calls = []
        # Hardware optimization tracks
        self.stt_load_calls = []
        self.stt_unload_calls = []
        self.llm_load_calls = []
        self.llm_unload_calls = []

history = MockHistory()
loaded_in_vram = set()

def reset_history():
    history.tts_speak_calls.clear()
    history.tts_stop_calls.clear()
    history.stt_transcribe_calls.clear()
    history.llm_generate_calls.clear()
    history.controller_handle_input_calls.clear()
    history.controller_start_calls.clear()
    history.wiki_retrieve_calls.clear()
    # Reset hardware optimization tracks
    history.stt_load_calls.clear()
    history.stt_unload_calls.clear()
    history.llm_load_calls.clear()
    history.llm_unload_calls.clear()
    loaded_in_vram.clear()
```

#### B. Update TTSEngine Mock
Modify the constructor of `TTSEngine` around lines 29-37 to store its configured device:
```python
class TTSEngine:
    def __init__(self):
        self._is_speaking = False
        self._lock = threading.Lock()
        self._speak_thread = None
        self._stop_event = threading.Event()
        self._current_speak_id = 0
        try:
            import voice_assistant.config as config
            self.device = getattr(config, "TTS_DEVICE", "cpu")
        except ImportError:
            self.device = "cpu"
```

#### C. Update STTEngine Mock
Replace the `STTEngine` implementation (around lines 88-115) with:
```python
class STTEngine:
    def __init__(self):
        self.transcriptions = {}
        self.default_transcription = "Simulated speech transcription"
        try:
            import voice_assistant.config as config
            dynamic_loading = getattr(config, "DYNAMIC_MODEL_LOADING", False)
            stt_device = getattr(config, "STT_DEVICE", "cuda")
        except ImportError:
            dynamic_loading = False
            stt_device = "cuda"
        self._is_model_loaded = not dynamic_loading
        self.device = stt_device

    def load_model(self) -> None:
        try:
            import voice_assistant.config as config
            stt_device = getattr(config, "STT_DEVICE", "cuda")
            dynamic_loading = getattr(config, "DYNAMIC_MODEL_LOADING", False)
        except ImportError:
            stt_device = "cuda"
            dynamic_loading = False
            
        self.device = stt_device
        if self.device == "cuda":
            if dynamic_loading and "LLMEngine" in loaded_in_vram:
                raise RuntimeError("VRAM Overflow: STTEngine and LLMEngine cannot be loaded in VRAM concurrently")
            loaded_in_vram.add("STTEngine")
        self._is_model_loaded = True
        history.stt_load_calls.append(True)

    def unload_model(self) -> None:
        loaded_in_vram.discard("STTEngine")
        self._is_model_loaded = False
        history.stt_unload_calls.append(True)

    def transcribe(self, audio_path_or_data) -> str:
        history.stt_transcribe_calls.append(audio_path_or_data)
        
        if not self._is_model_loaded:
            raise RuntimeError("Model not loaded for STTEngine")

        if audio_path_or_data is None:
            raise TypeError("Audio input cannot be None")
        
        if isinstance(audio_path_or_data, str):
            if not audio_path_or_data:
                raise ValueError("Audio path cannot be empty")
            if audio_path_or_data.endswith(".err"):
                raise ValueError("Simulated format error")
            if "non_existent" in audio_path_or_data and not os.path.exists(audio_path_or_data):
                raise FileNotFoundError(f"File not found: {audio_path_or_data}")
            return self.transcriptions.get(audio_path_or_data, self.default_transcription)
        
        if isinstance(audio_path_or_data, bytes):
            if len(audio_path_or_data) == 0:
                return ""
            return self.default_transcription
 
        raise ValueError("Invalid audio input type")
```

#### D. Update LLMEngine Mock
Replace the `LLMEngine` implementation (around lines 117-152) with:
```python
class LLMEngine:
    def __init__(self):
        self.responses = {}
        self.default_response = "Simulated assistant response"
        self.simulate_offline = False
        try:
            import voice_assistant.config as config
            dynamic_loading = getattr(config, "DYNAMIC_MODEL_LOADING", False)
            llm_device = getattr(config, "LLM_DEVICE", "cuda")
        except ImportError:
            dynamic_loading = False
            llm_device = "cuda"
        self._is_model_loaded = not dynamic_loading
        self.device = llm_device

    def load_model(self) -> None:
        try:
            import voice_assistant.config as config
            llm_device = getattr(config, "LLM_DEVICE", "cuda")
            dynamic_loading = getattr(config, "DYNAMIC_MODEL_LOADING", False)
        except ImportError:
            llm_device = "cuda"
            dynamic_loading = False
            
        self.device = llm_device
        if self.device == "cuda":
            if dynamic_loading and "STTEngine" in loaded_in_vram:
                raise RuntimeError("VRAM Overflow: STTEngine and LLMEngine cannot be loaded in VRAM concurrently")
            loaded_in_vram.add("LLMEngine")
        self._is_model_loaded = True
        history.llm_load_calls.append(True)

    def unload_model(self) -> None:
        loaded_in_vram.discard("LLMEngine")
        self._is_model_loaded = False
        history.llm_unload_calls.append(True)

    def generate_response(self, prompt: str, context: list = None, retrieval_context: str = "") -> str:
        if context is None:
            context = []
        history.llm_generate_calls.append((prompt, context, retrieval_context))
        
        if not self._is_model_loaded:
            raise RuntimeError("Model not loaded for LLMEngine")

        if self.simulate_offline:
            raise ConnectionError("Simulated LLM service offline")
        if prompt is None:
            raise TypeError("Prompt cannot be None")
        if prompt == "":
            raise ValueError("Prompt cannot be empty")
        if not isinstance(context, list):
            raise TypeError("Context must be a list")
        for item in context:
            if not isinstance(item, dict):
                raise TypeError("Context elements must be dictionaries")

        if prompt in self.responses:
            response = self.responses[prompt]
        elif "hello" in prompt.lower():
            response = "Hello! How can I help you?"
        elif "dừng lại" in prompt.lower() or "stop" in prompt.lower():
            response = "Stopping playback."
        else:
            response = f"{self.default_response} to: {prompt}"

        if retrieval_context:
            response = f"{response} [Retrieval Context: {retrieval_context}]"
            
        return response
```

#### E. Update AssistantController Mock
Replace the `handle_input` function in mock `AssistantController` (around lines 199-241) to execute load and unload transitions when dynamic loading is active:
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

        try:
            import voice_assistant.config as config
            dynamic_loading = getattr(config, "DYNAMIC_MODEL_LOADING", False)
        except ImportError:
            dynamic_loading = False

        if input_type in ("voice", "audio"):
            if dynamic_loading:
                self.stt_engine.load_model()
            try:
                prompt = self.stt_engine.transcribe(content)
            finally:
                if dynamic_loading:
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
            self.llm_engine.load_model()
        try:
            response = self.llm_engine.generate_response(prompt, self.context, retrieval_context=retrieval_context)
        finally:
            if dynamic_loading:
                self.llm_engine.unload_model()
        
        self.context.append({"role": "user", "content": prompt})
        self.context.append({"role": "assistant", "content": response})

        volume = 0.5
        try:
            import voice_assistant.config as config
            volume = config.DEFAULT_VOLUME
        except Exception:
            pass
            
        self.tts_engine.speak(response, volume=volume)
```

#### F. Injected Config Module Setup
Update lines 294-300 of `tests/mock_assistant.py` to pre-populate configuration default parameters:
```python
    va_config = ModuleType("voice_assistant.config")
    va_config.DEFAULT_VOLUME = 0.5
    va_config.OFFLINE_MODE = True
    va_config.DEVICE = "cuda"
    va_config.DYNAMIC_MODEL_LOADING = False
    va_config.STT_DEVICE = "cuda"
    va_config.LLM_DEVICE = "cuda"
    va_config.TTS_DEVICE = "cpu"
    sys.modules["voice_assistant.config"] = va_config
    va.config = va_config
```

---

### Step 3: Create `tests/test_optimization.py`
Create a new file `tests/test_optimization.py` containing the 14 E2E test cases:
```python
import os
import sys
import unittest
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tests.mock_assistant as mock_assistant
from voice_assistant.stt import STTEngine
from voice_assistant.llm import LLMEngine
from voice_assistant.tts import TTSEngine
from voice_assistant.controller import AssistantController
import voice_assistant.config as config

class TestHardwareOptimization(unittest.TestCase):
    def setUp(self):
        mock_assistant.reset_history()
        config.DEFAULT_VOLUME = 0.5
        config.DYNAMIC_MODEL_LOADING = False
        config.STT_DEVICE = "cuda"
        config.LLM_DEVICE = "cuda"
        config.TTS_DEVICE = "cpu"

    def tearDown(self):
        pass

    # ==========================================
    # Tier 1: Happy-Path Coverage (5 cases)
    # ==========================================
    
    def test_stt_load_unload(self):
        """Tier 1: Verify STTEngine load_model() and unload_model() work cleanly."""
        engine = STTEngine()
        config.DYNAMIC_MODEL_LOADING = True
        engine._is_model_loaded = False
        
        self.assertFalse(engine._is_model_loaded)
        engine.load_model()
        self.assertTrue(engine._is_model_loaded)
        self.assertIn("STTEngine", mock_assistant.loaded_in_vram)
        
        engine.unload_model()
        self.assertFalse(engine._is_model_loaded)
        self.assertNotIn("STTEngine", mock_assistant.loaded_in_vram)
        self.assertEqual(len(mock_assistant.history.stt_load_calls), 1)
        self.assertEqual(len(mock_assistant.history.stt_unload_calls), 1)

    def test_llm_load_unload(self):
        """Tier 1: Verify LLMEngine load_model() and unload_model() work cleanly."""
        engine = LLMEngine()
        config.DYNAMIC_MODEL_LOADING = True
        engine._is_model_loaded = False
        
        self.assertFalse(engine._is_model_loaded)
        engine.load_model()
        self.assertTrue(engine._is_model_loaded)
        self.assertIn("LLMEngine", mock_assistant.loaded_in_vram)
        
        engine.unload_model()
        self.assertFalse(engine._is_model_loaded)
        self.assertNotIn("LLMEngine", mock_assistant.loaded_in_vram)
        self.assertEqual(len(mock_assistant.history.llm_load_calls), 1)
        self.assertEqual(len(mock_assistant.history.llm_unload_calls), 1)

    def test_stt_device_config(self):
        """Tier 1: Verify STTEngine reads device config during load."""
        config.STT_DEVICE = "cpu"
        engine = STTEngine()
        config.DYNAMIC_MODEL_LOADING = True
        engine.load_model()
        self.assertEqual(engine.device, "cpu")
        self.assertNotIn("STTEngine", mock_assistant.loaded_in_vram)

    def test_tts_device_config(self):
        """Tier 1: Verify TTSEngine device config is set correctly."""
        config.TTS_DEVICE = "cpu"
        engine = TTSEngine()
        self.assertEqual(engine.device, "cpu")

    def test_controller_dynamic_loading_flow(self):
        """Tier 1: Verify dynamic model loading schedule in AssistantController."""
        config.DYNAMIC_MODEL_LOADING = True
        controller = AssistantController()
        
        controller.handle_input("voice", "test_audio.wav")
        
        self.assertEqual(len(mock_assistant.history.stt_load_calls), 1)
        self.assertEqual(len(mock_assistant.history.stt_unload_calls), 1)
        self.assertEqual(len(mock_assistant.history.llm_load_calls), 1)
        self.assertEqual(len(mock_assistant.history.llm_unload_calls), 1)

    # ==========================================
    # Tier 2: Boundary & Edge Cases (5 cases)
    # ==========================================

    def test_stt_transcribe_without_load(self):
        """Tier 2: STTEngine transcription fails if the model is not loaded."""
        config.DYNAMIC_MODEL_LOADING = True
        engine = STTEngine()
        engine._is_model_loaded = False
        
        with self.assertRaises(RuntimeError) as ctx:
            engine.transcribe("test_audio.wav")
        self.assertIn("Model not loaded", str(ctx.exception))

    def test_llm_generate_without_load(self):
        """Tier 2: LLMEngine response generation fails if the model is not loaded."""
        config.DYNAMIC_MODEL_LOADING = True
        engine = LLMEngine()
        engine._is_model_loaded = False
        
        with self.assertRaises(RuntimeError) as ctx:
            engine.generate_response("hello")
        self.assertIn("Model not loaded", str(ctx.exception))

    def test_vram_safety_violation(self):
        """Tier 2: Verify exception is raised when both STT & LLM are in VRAM."""
        config.DYNAMIC_MODEL_LOADING = True
        stt = STTEngine()
        llm = LLMEngine()
        
        stt.load_model()
        with self.assertRaises(RuntimeError) as ctx:
            llm.load_model()
        self.assertIn("VRAM Overflow", str(ctx.exception))

    def test_vram_safety_cpu_offload(self):
        """Tier 2: Verify concurrency is allowed if STT is offloaded to CPU."""
        config.DYNAMIC_MODEL_LOADING = True
        config.STT_DEVICE = "cpu"
        config.LLM_DEVICE = "cuda"
        
        stt = STTEngine()
        llm = LLMEngine()
        
        stt.load_model()
        llm.load_model()
        self.assertTrue(stt._is_model_loaded)
        self.assertTrue(llm._is_model_loaded)

    def test_dynamic_loading_disabled_vram_concurrency(self):
        """Tier 2: Concurrency is allowed if DYNAMIC_MODEL_LOADING is disabled."""
        config.DYNAMIC_MODEL_LOADING = False
        config.STT_DEVICE = "cuda"
        config.LLM_DEVICE = "cuda"
        
        stt = STTEngine()
        llm = LLMEngine()
        
        stt.load_model()
        llm.load_model()
        self.assertTrue(stt._is_model_loaded)
        self.assertTrue(llm._is_model_loaded)

    # ==========================================
    # Tier 3: Cross-Feature Combinations (2 cases)
    # ==========================================

    def test_dynamic_loading_rag_combination(self):
        """Tier 3: Verify dynamic loading works when RAG triggers for text query."""
        config.DYNAMIC_MODEL_LOADING = True
        controller = AssistantController()
        
        controller.handle_input("text", "Explain Controller")
        
        self.assertEqual(len(mock_assistant.history.stt_load_calls), 0)
        self.assertEqual(len(mock_assistant.history.stt_unload_calls), 0)
        self.assertEqual(len(mock_assistant.history.llm_load_calls), 1)
        self.assertEqual(len(mock_assistant.history.llm_unload_calls), 1)
        self.assertEqual(len(mock_assistant.history.wiki_retrieve_calls), 1)

    def test_dynamic_loading_with_playback_interruption(self):
        """Tier 3: Verify dynamic loading and VRAM state cleanups under interruption."""
        config.DYNAMIC_MODEL_LOADING = True
        controller = AssistantController()
        
        controller.tts_engine.speak("This is a very long briefing text that should be interrupted.", volume=0.5)
        self.assertTrue(controller.tts_engine.is_speaking())
        
        controller.handle_input("voice", "test_interrupt.wav")
        
        self.assertEqual(len(mock_assistant.history.stt_load_calls), 1)
        self.assertEqual(len(mock_assistant.history.llm_load_calls), 1)
        self.assertFalse(controller.stt_engine._is_model_loaded)
        self.assertFalse(controller.llm_engine._is_model_loaded)

    # ==========================================
    # Tier 4: Real-World Workflow Scenarios (2 cases)
    # ==========================================

    def test_scenario_low_vram_device_scheduling(self):
        """Tier 4: Scenario 1 - Simulating conversational turns on low-VRAM setup."""
        config.DYNAMIC_MODEL_LOADING = True
        config.STT_DEVICE = "cuda"
        config.LLM_DEVICE = "cuda"
        controller = AssistantController()
        
        for i in range(3):
            controller.handle_input("voice", f"turn_{i}_audio.wav")
            self.assertNotIn("STTEngine", mock_assistant.loaded_in_vram)
            self.assertNotIn("LLMEngine", mock_assistant.loaded_in_vram)
            
        self.assertEqual(len(mock_assistant.history.stt_load_calls), 3)
        self.assertEqual(len(mock_assistant.history.stt_unload_calls), 3)
        self.assertEqual(len(mock_assistant.history.llm_load_calls), 3)
        self.assertEqual(len(mock_assistant.history.llm_unload_calls), 3)

    def test_scenario_heterogeneous_device_allocation(self):
        """Tier 4: Scenario 2 - Heterogeneous device allocation (STT on CPU, LLM on CUDA)."""
        config.DYNAMIC_MODEL_LOADING = True
        config.STT_DEVICE = "cpu"
        config.LLM_DEVICE = "cuda"
        controller = AssistantController()
        
        controller.handle_input("voice", "query_audio.wav")
        
        self.assertEqual(len(mock_assistant.history.stt_load_calls), 1)
        self.assertEqual(len(mock_assistant.history.llm_load_calls), 1)
        self.assertEqual(controller.stt_engine.device, "cpu")
        self.assertEqual(controller.llm_engine.device, "cuda")
        self.assertNotIn("STTEngine", mock_assistant.loaded_in_vram)
```

---

### Step 4: Update `tests/run_tests.py`
Update `tests/run_tests.py` to discover the new test suite file:
```python
    # Discover all tests matching 'test_tier*.py', 'test_rag.py', and 'test_optimization.py'
    loader = unittest.TestLoader()
    suite_tier = loader.discover(start_dir=tests_dir, pattern="test_tier*.py")
    suite_rag = loader.discover(start_dir=tests_dir, pattern="test_rag.py")
    suite_opt = loader.discover(start_dir=tests_dir, pattern="test_optimization.py")
    suite = unittest.TestSuite([suite_tier, suite_rag, suite_opt])
```

---

### Step 5: Update `TEST_INFRA.md`
Modify `TEST_INFRA.md` to document the new optimization feature (Feature 7) and coverage metrics. Update Section 5 "Coverage Thresholds" to reflect 89 cases total (75 original + 14 new optimization cases).

---

### Step 6: Update `TEST_READY.md`
Once tests are successfully run, update the verification log, status, and summary counts to state that all 89 test cases have run and passed successfully.
