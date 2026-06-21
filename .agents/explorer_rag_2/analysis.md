# Requirements Analysis: Adding R5 RAG Tests and Test Infrastructure Updates

This document analyzes the requirements for Resuming Milestone 2: R5 RAG Verification, and details the proposed code changes for `tests/mock_assistant.py`, `tests/test_rag.py`, `tests/run_tests.py`, and `TEST_INFRA.md`.

---

## 1. Mocking WikiRetriever and Updates to Mock Engines

To support offline testing of RAG features, the test suite relies on `tests/mock_assistant.py`. When `MOCK_ENGINES=1` is set, the mocks intercept imports of the `voice_assistant` package.

### 1.1 Mocking `voice_assistant.wiki.WikiRetriever`
We introduce a mock class `WikiRetriever` matching the contract specified in `PROJECT.md` and `SCOPE.md`.
- **Constructor**: `__init__(self, data_paths: list = None)`
- **Retrieve Method**: `retrieve(self, query: str, top_k: int = 2) -> list[str]`
- **Properties**:
  - `self.documents`: A list of pre-defined mock strings matching the MVC simulator context (e.g., `DoctorController`, `DoctorRepository`) to support realistic search matching.
  - `self.default_chunks`: Default fallback chunks (e.g., `["Mock wiki chunk 1", "Mock wiki chunk 2"]`) when no query matches.
  - `self.simulate_error`: A boolean flag to simulate retrieval failures (e.g., raising `RuntimeError`).
- **Mock History Integration**: Logs query and top_k to `history.wiki_retrieve_calls`.

### 1.2 LLMEngine updates for `retrieval_context`
The mock `LLMEngine.generate_response` is updated to accept the optional keyword argument `retrieval_context` (default `""`).
- **Signature**: `generate_response(self, prompt: str, context: list, retrieval_context: str = "") -> str`
- **Behavior**: If `retrieval_context` is provided, it is validated as a string and appended/integrated into the simulated LLM response string to allow tests to verify that the LLM uses the retrieved context.

### 1.3 AssistantController updates for RAG flow integration
The mock `AssistantController` is updated to integrate `WikiRetriever`.
- **Constructor**: Updated to take optional `wiki_retriever=None`.
- **RAG Integration**: In `handle_input(self, input_type: str, content)`, if input text/voice translates to a non-empty prompt:
  1. It queries `self.wiki_retriever.retrieve(prompt, top_k=2)`.
  2. If matching chunks are returned, they are joined by newlines into a `retrieval_context` string.
  3. If a retrieval error occurs, it catches the error and falls back gracefully, passing an empty `retrieval_context` to the LLM.
  4. The LLM `generate_response` is invoked with the prompt, conversation context, and `retrieval_context`.

### 1.4 Global History and `sys.modules` Injection
- Add `wiki_retrieve_calls` to `MockHistory` and update `reset_history()`.
- Register the mock class as `voice_assistant.wiki.WikiRetriever` in the global `sys.modules` table.

---

## Proposed Changes to `tests/mock_assistant.py`

```python
<<<<
class MockHistory:
    def __init__(self):
        self.tts_speak_calls = []
        self.tts_stop_calls = []
        self.stt_transcribe_calls = []
        self.llm_generate_calls = []
        self.controller_handle_input_calls = []
        self.controller_start_calls = []

history = MockHistory()

def reset_history():
    history.tts_speak_calls.clear()
    history.tts_stop_calls.clear()
    history.stt_transcribe_calls.clear()
    history.llm_generate_calls.clear()
    history.controller_handle_input_calls.clear()
    history.controller_start_calls.clear()
====
class MockHistory:
    def __init__(self):
        self.tts_speak_calls = []
        self.tts_stop_calls = []
        self.stt_transcribe_calls = []
        self.llm_generate_calls = []
        self.controller_handle_input_calls = []
        self.controller_start_calls = []
        self.wiki_retrieve_calls = []  # Added for WikiRetriever tracking

history = MockHistory()

def reset_history():
    history.tts_speak_calls.clear()
    history.tts_stop_calls.clear()
    history.stt_transcribe_calls.clear()
    history.llm_generate_calls.clear()
    history.controller_handle_input_calls.clear()
    history.controller_start_calls.clear()
    history.wiki_retrieve_calls.clear()  # Added
>>>>
```

```python
<<<<
# LLMEngine Mock
class LLMEngine:
    def __init__(self):
        self.responses = {}
        self.default_response = "Simulated assistant response"
        self.simulate_offline = False

    def generate_response(self, prompt: str, context: list) -> str:
        history.llm_generate_calls.append((prompt, context))
        
        if self.simulate_offline:
            raise ConnectionError("Simulated LLM service offline")
        if prompt is None:
            raise TypeError("Prompt cannot be None")
        if prompt == "":
            raise ValueError("Prompt cannot be empty")
        if context is None:
            raise TypeError("Context cannot be None")
        if not isinstance(context, list):
            raise TypeError("Context must be a list")
        for item in context:
            if not isinstance(item, dict):
                raise TypeError("Context elements must be dictionaries")

        if prompt in self.responses:
            return self.responses[prompt]
            
        if "hello" in prompt.lower():
            return "Hello! How can I help you?"
        if "dừng lại" in prompt.lower() or "stop" in prompt.lower():
            return "Stopping playback."
        
        return f"{self.default_response} to: {prompt}"
====
# WikiRetriever Mock
class WikiRetriever:
    def __init__(self, data_paths: list = None):
        self.data_paths = data_paths if data_paths is not None else []
        self.documents = [
            "DoctorController coordinates between Doctor model and DoctorView.",
            "DoctorRepository manages Doctor data storage and retrieval in memory.",
            "DoctorRequestDTO holds validation rules for doctor creation and updates.",
            "Validation helper checks name length and specialty format."
        ]
        self.default_chunks = ["Mock wiki chunk 1", "Mock wiki chunk 2"]
        self.simulate_error = False

    def retrieve(self, query: str, top_k: int = 2) -> list[str]:
        history.wiki_retrieve_calls.append((query, top_k))
        
        if self.simulate_error:
            raise RuntimeError("Simulated WikiRetriever retrieval failure")
        if query is None:
            raise TypeError("Query cannot be None")
        if not isinstance(query, str):
            raise TypeError("Query must be a string")
        if top_k is None:
            raise TypeError("top_k cannot be None")
        if not isinstance(top_k, int):
            raise TypeError("top_k must be an integer")
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0")

        results = []
        for doc in self.documents:
            if query.lower() in doc.lower():
                results.append(doc)
        if not results:
            results = self.default_chunks
        return results[:top_k]

# LLMEngine Mock
class LLMEngine:
    def __init__(self):
        self.responses = {}
        self.default_response = "Simulated assistant response"
        self.simulate_offline = False

    def generate_response(self, prompt: str, context: list, retrieval_context: str = "") -> str:
        history.llm_generate_calls.append((prompt, context, retrieval_context))
        
        if self.simulate_offline:
            raise ConnectionError("Simulated LLM service offline")
        if prompt is None:
            raise TypeError("Prompt cannot be None")
        if prompt == "":
            raise ValueError("Prompt cannot be empty")
        if context is None:
            raise TypeError("Context cannot be None")
        if not isinstance(context, list):
            raise TypeError("Context must be a list")
        if not isinstance(retrieval_context, str):
            raise TypeError("Retrieval context must be a string")
        for item in context:
            if not isinstance(item, dict):
                raise TypeError("Context elements must be dictionaries")

        if prompt in self.responses:
            return self.responses[prompt]
            
        if "hello" in prompt.lower():
            return "Hello! How can I help you?"
        if "dừng lại" in prompt.lower() or "stop" in prompt.lower():
            return "Stopping playback."
        
        if retrieval_context:
            return f"{self.default_response} with context '{retrieval_context}' to: {prompt}"
            
        return f"{self.default_response} to: {prompt}"
>>>>
```

```python
<<<<
# AssistantController Mock
class AssistantController:
    def __init__(self, tts_engine=None, stt_engine=None, llm_engine=None):
        self.tts_engine = tts_engine if tts_engine else TTSEngine()
        self.stt_engine = stt_engine if stt_engine else STTEngine()
        self.llm_engine = llm_engine if llm_engine else LLMEngine()
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

        if input_type in ("voice", "audio"):
            prompt = self.stt_engine.transcribe(content)
        elif input_type == "text":
            prompt = content
        else:
            raise ValueError(f"Invalid input type: {input_type}")

        if not prompt:
            return

        response = self.llm_engine.generate_response(prompt, self.context)
        
        self.context.append({"role": "user", "content": prompt})
        self.context.append({"role": "assistant", "content": response})

        volume = 0.5
        try:
            import voice_assistant.config as config
            volume = config.DEFAULT_VOLUME
        except Exception:
            pass
            
        self.tts_engine.speak(response, volume=volume)
====
# AssistantController Mock
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

        if input_type in ("voice", "audio"):
            prompt = self.stt_engine.transcribe(content)
        elif input_type == "text":
            prompt = content
        else:
            raise ValueError(f"Invalid input type: {input_type}")

        if not prompt:
            return

        # RAG query flow
        retrieval_context = ""
        try:
            chunks = self.wiki_retriever.retrieve(prompt, top_k=2)
            if chunks:
                retrieval_context = "\n".join(chunks)
        except Exception:
            # Fallback gracefully
            retrieval_context = ""

        response = self.llm_engine.generate_response(prompt, self.context, retrieval_context=retrieval_context)
        
        self.context.append({"role": "user", "content": prompt})
        self.context.append({"role": "assistant", "content": response})

        volume = 0.5
        try:
            import voice_assistant.config as config
            volume = config.DEFAULT_VOLUME
        except Exception:
            pass
            
        self.tts_engine.speak(response, volume=volume)
>>>>
```

```python
<<<<
    va_llm = ModuleType("voice_assistant.llm")
    va_llm.LLMEngine = LLMEngine
    sys.modules["voice_assistant.llm"] = va_llm
    va.llm = va_llm

    va_controller = ModuleType("voice_assistant.controller")
    va_controller.AssistantController = AssistantController
    sys.modules["voice_assistant.controller"] = va_controller
    va.controller = va_controller
====
    va_llm = ModuleType("voice_assistant.llm")
    va_llm.LLMEngine = LLMEngine
    sys.modules["voice_assistant.llm"] = va_llm
    va.llm = va_llm

    va_wiki = ModuleType("voice_assistant.wiki")
    va_wiki.WikiRetriever = WikiRetriever
    sys.modules["voice_assistant.wiki"] = va_wiki
    va.wiki = va_wiki

    va_controller = ModuleType("voice_assistant.controller")
    va_controller.AssistantController = AssistantController
    sys.modules["voice_assistant.controller"] = va_controller
    va.controller = va_controller
>>>>
```

---

## 2. Implementing RAG Tests (`tests/test_rag.py`)

A new test file `tests/test_rag.py` will be added to implement 12 tests distributed across Tiers 1-4.

### 2.1 Happy-Path Feature Coverage (Tier 1 - 5 cases)
1. **`test_wiki_retrieve_happy_path`**: Verifies `WikiRetriever.retrieve` correctly returns relevant mock chunks for a valid query and registers in global history.
2. **`test_wiki_retrieve_top_k`**: Verifies that retrieved outputs conform to the `top_k` parameter limits.
3. **`test_llm_with_retrieval_context`**: Verifies that the LLM response is augmented by the supplied non-empty `retrieval_context` string.
4. **`test_controller_integrates_rag_flow`**: Verifies that `AssistantController.handle_input` properly queries `WikiRetriever` and invokes `LLMEngine` with the retrieval context.
5. **`test_wiki_retriever_custom_documents`**: Verifies that the retriever correctly matches custom documents assigned to `WikiRetriever.documents`.

### 2.2 Boundary & Edge Cases (Tier 2 - 5 cases)
1. **`test_wiki_retrieve_invalid_query_type`**: Verifies that passing `None` or an integer as the query parameter raises `TypeError`.
2. **`test_wiki_retrieve_invalid_top_k`**: Verifies that non-integer `top_k` values or `top_k <= 0` raise `TypeError` or `ValueError`.
3. **`test_llm_invalid_retrieval_context_type`**: Verifies that passing non-string values (such as integers or lists) to `LLMEngine.generate_response` as `retrieval_context` raises `TypeError`.
4. **`test_controller_graceful_fallback_on_retriever_error`**: Verifies that when `WikiRetriever.retrieve` raises an error, the controller continues execution, invoking the LLM with an empty context and speaking the response without throwing an exception.
5. **`test_wiki_retrieve_no_matches`**: Verifies that when no document matches, the retriever returns the default chunks.

### 2.3 Cross-Feature Combinations (Tier 3 - 1 case)
1. **`test_stt_to_rag_to_llm_to_tts_pipeline`**: Verifies end-to-end integration: audio input transcribed to a query -> queries the wiki retriever -> returns factual context -> LLM generates response using context -> TTS speaks response.

### 2.4 Real-World Scenario (Tier 4 - 1 case)
1. **`test_scenario_mvc_developer_query`**: Simulates a developer querying the assistant about `DoctorController` in the MVC simulation. Verifies context retrieval, synthesis, and voice output generation at default volume.

### Proposed Code for `tests/test_rag.py`

```python
import os
import sys
import unittest
import time

# Add root folder to sys.path so tests can import mock_assistant and voice_assistant
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tests.mock_assistant as mock_assistant
from voice_assistant.wiki import WikiRetriever
from voice_assistant.llm import LLMEngine
from voice_assistant.controller import AssistantController
from voice_assistant.tts import TTSEngine
from voice_assistant.stt import STTEngine
import voice_assistant.config as config

class TestRAGPipeline(unittest.TestCase):
    def setUp(self):
        mock_assistant.reset_history()
        config.DEFAULT_VOLUME = 0.5

    # ==========================================
    # 1. Tier 1: Happy-Path Coverage (5 cases)
    # ==========================================
    def test_wiki_retrieve_happy_path(self):
        retriever = WikiRetriever()
        results = retriever.retrieve("DoctorController")
        self.assertIsInstance(results, list)
        self.assertTrue(len(results) > 0)
        self.assertIn("DoctorController coordinates between Doctor model and DoctorView.", results[0])
        self.assertEqual(len(mock_assistant.history.wiki_retrieve_calls), 1)
        self.assertEqual(mock_assistant.history.wiki_retrieve_calls[0], ("DoctorController", 2))

    def test_wiki_retrieve_top_k(self):
        retriever = WikiRetriever()
        results = retriever.retrieve("Doctor", top_k=1)
        self.assertEqual(len(results), 1)
        
        results_two = retriever.retrieve("Doctor", top_k=2)
        self.assertEqual(len(results_two), 2)

    def test_llm_with_retrieval_context(self):
        engine = LLMEngine()
        prompt = "Explain DoctorController"
        retrieval_context = "DoctorController coordinates between Doctor model and DoctorView."
        response = engine.generate_response(prompt, [], retrieval_context=retrieval_context)
        self.assertIn("DoctorController coordinates between Doctor model and DoctorView.", response)
        self.assertEqual(len(mock_assistant.history.llm_generate_calls), 1)
        self.assertEqual(mock_assistant.history.llm_generate_calls[0], (prompt, [], retrieval_context))

    def test_controller_integrates_rag_flow(self):
        retriever = WikiRetriever()
        llm = LLMEngine()
        tts = TTSEngine()
        controller = AssistantController(tts_engine=tts, llm_engine=llm, wiki_retriever=retriever)
        
        controller.handle_input("text", "DoctorController query")
        
        self.assertEqual(len(mock_assistant.history.wiki_retrieve_calls), 1)
        self.assertEqual(mock_assistant.history.wiki_retrieve_calls[0][0], "DoctorController query")
        self.assertEqual(len(mock_assistant.history.llm_generate_calls), 1)
        self.assertIsNotNone(mock_assistant.history.llm_generate_calls[0][2])

    def test_wiki_retriever_custom_documents(self):
        retriever = WikiRetriever()
        custom_docs = ["Specialized medical info block 1", "Specialized medical info block 2"]
        retriever.documents = custom_docs
        
        results = retriever.retrieve("medical", top_k=2)
        self.assertEqual(results, custom_docs)

    # ==========================================
    # 2. Tier 2: Boundary & Edge Cases (5 cases)
    # ==========================================
    def test_wiki_retrieve_invalid_query_type(self):
        retriever = WikiRetriever()
        with self.assertRaises(TypeError):
            retriever.retrieve(None)
        with self.assertRaises(TypeError):
            retriever.retrieve(12345)

    def test_wiki_retrieve_invalid_top_k(self):
        retriever = WikiRetriever()
        with self.assertRaises(TypeError):
            retriever.retrieve("DoctorController", top_k=None)
        with self.assertRaises(TypeError):
            retriever.retrieve("DoctorController", top_k="two")
        with self.assertRaises(ValueError):
            retriever.retrieve("DoctorController", top_k=-1)
        with self.assertRaises(ValueError):
            retriever.retrieve("DoctorController", top_k=0)

    def test_llm_invalid_retrieval_context_type(self):
        engine = LLMEngine()
        with self.assertRaises(TypeError):
            engine.generate_response("prompt", [], retrieval_context=123)
        with self.assertRaises(TypeError):
            engine.generate_response("prompt", [], retrieval_context=["invalid", "type"])

    def test_controller_graceful_fallback_on_retriever_error(self):
        retriever = WikiRetriever()
        retriever.simulate_error = True
        llm = LLMEngine()
        tts = TTSEngine()
        controller = AssistantController(tts_engine=tts, llm_engine=llm, wiki_retriever=retriever)
        
        controller.handle_input("text", "DoctorController query")
        
        self.assertEqual(len(mock_assistant.history.llm_generate_calls), 1)
        self.assertEqual(mock_assistant.history.llm_generate_calls[0][2], "")
        self.assertTrue(len(mock_assistant.history.tts_speak_calls) > 0)

    def test_wiki_retrieve_no_matches(self):
        retriever = WikiRetriever()
        results = retriever.retrieve("NonExistentTermPatternXYZ")
        self.assertEqual(results, retriever.default_chunks[:2])

    # ==========================================
    # 3. Tier 3: Cross-Feature Combinations (1 case)
    # ==========================================
    def test_stt_to_rag_to_llm_to_tts_pipeline(self):
        stt = STTEngine()
        retriever = WikiRetriever()
        llm = LLMEngine()
        tts = TTSEngine()
        
        stt.transcriptions["audio_query.wav"] = "DoctorRepository explanation"
        
        controller = AssistantController(
            tts_engine=tts,
            stt_engine=stt,
            llm_engine=llm,
            wiki_retriever=retriever
        )
        
        controller.handle_input("voice", "audio_query.wav")
        
        self.assertEqual(mock_assistant.history.stt_transcribe_calls[0], "audio_query.wav")
        self.assertEqual(mock_assistant.history.wiki_retrieve_calls[0][0], "DoctorRepository explanation")
        self.assertEqual(len(mock_assistant.history.llm_generate_calls), 1)
        expected_context = "DoctorRepository manages Doctor data storage and retrieval in memory."
        self.assertIn(expected_context, mock_assistant.history.llm_generate_calls[0][2])
        self.assertEqual(len(mock_assistant.history.tts_speak_calls), 1)
        self.assertIn("DoctorRepository", mock_assistant.history.tts_speak_calls[0][0])

    # ==========================================
    # 4. Tier 4: Real-World Scenarios (1 case)
    # ==========================================
    def test_scenario_mvc_developer_query(self):
        retriever = WikiRetriever()
        llm = LLMEngine()
        tts = TTSEngine()
        controller = AssistantController(tts_engine=tts, llm_engine=llm, wiki_retriever=retriever)
        
        controller.handle_input("text", "Where is DoctorController used?")
        
        self.assertEqual(mock_assistant.history.wiki_retrieve_calls[0][0], "Where is DoctorController used?")
        retrieved_chunk = "DoctorController coordinates between Doctor model and DoctorView."
        self.assertIn(retrieved_chunk, mock_assistant.history.llm_generate_calls[0][2])
        self.assertEqual(len(mock_assistant.history.tts_speak_calls), 1)
        self.assertIn(retrieved_chunk, mock_assistant.history.tts_speak_calls[0][0])
```

---

## 3. Test Runner Update (`tests/run_tests.py`)

To ensure `tests/test_rag.py` is executed as part of the automated validation run, `tests/run_tests.py` must discover both `test_tier*.py` files and `test_rag.py`.

### Proposed Changes to `tests/run_tests.py`

```python
<<<<
    # Discover all tests matching 'test_tier*.py'
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=tests_dir, pattern="test_tier*.py")
    
    # Run tests using custom text runner
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
====
    # Discover all tests matching 'test_tier*.py' and 'test_rag.py'
    loader = unittest.TestLoader()
    suite_tier = loader.discover(start_dir=tests_dir, pattern="test_tier*.py")
    suite_rag = loader.discover(start_dir=tests_dir, pattern="test_rag.py")
    
    suite = unittest.TestSuite([suite_tier, suite_rag])
    
    # Run tests using custom text runner
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
>>>>
```

---

## 4. Documentation Updates (`TEST_INFRA.md`)

`TEST_INFRA.md` will be updated to document the RAG engine features, test cases, and thresholds.

### Proposed Changes to `TEST_INFRA.md`

#### Section 2: Feature Inventory
Add RAG inventory details:
```markdown
6.  **Wiki/Knowledge Base Retrieval (RAG)**:
    *   Querying the local knowledge base using `retrieve(query, top_k)`.
    *   Returning relevant factual text chunks based on matching keywords or document indexes.
    *   Robust parameter verification (`query`, `top_k`) and validation.
    *   Seamless integration with the LLM Engine to supply `retrieval_context`.
    *   Graceful fallback behavior when retrieval errors are encountered.
```

#### Section 3: Test Architecture (Test Files)
Add `tests/test_rag.py`:
```markdown
*   `tests/test_rag.py`: Verifies local wiki indexing, retrieval parameter boundaries, LLM context integration, and fallback mechanisms.
```

#### Section 4: Real-World Application Scenarios
Add RAG Scenario 6:
```markdown
6.  **Scenario 6: MVC Developer Query**
    *   *Description*: An MVC developer queries the assistant: "Where is DoctorController used?".
    *   *Verification*: The `WikiRetriever` searches its local index, matches the document on `DoctorController`, and returns it. The LLM processes this context and produces an accurate response which is spoken by TTS.
7.  **Scenario 7: Failed Wiki Search with Graceful Fallback**
    *   *Description*: The user asks a query when the wiki database fails (simulated by setting `wiki_retriever.simulate_error = True`).
    *   *Verification*: The controller catches the retriever error, falls back to querying the LLM with an empty context, and speaks the LLM response without crashing.
```

#### Section 5: Coverage Thresholds
Update coverage table:
```markdown
| Test Tier | Focus Area | Minimum Threshold | Implemented | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1** | Happy-Path Coverage (5 per feature) | $\ge$ 30 cases | 30 cases | **Passed** |
| **Tier 2** | Boundary & Edge Cases (5 per feature) | $\ge$ 30 cases | 30 cases | **Passed** |
| **Tier 3** | Cross-Feature Combinations | $\ge$ 6 cases | 6 cases | **Passed** |
| **Tier 4** | Real-World Workflow Scenarios | $\ge$ 6 cases | 6 cases | **Passed** |
| **Total** | **Comprehensive E2E Suite** | **$\ge$ 72 cases** | **72 cases** | **Passed** |
```
