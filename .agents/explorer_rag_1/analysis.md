# Requirements Analysis for R5 RAG Tests & Mock Assistant Updates

This document analyzes the requirements for introducing R5 RAG tests and updating the testing infrastructure and runner to support the local knowledge retriever (`voice_assistant.wiki.WikiRetriever`) and retrieval context augmentation.

---

## 1. Mocking RAG Components in `tests/mock_assistant.py`

To verify the RAG system under mock execution, we must update the mock infrastructure in `tests/mock_assistant.py` to support `WikiRetriever` and coordinate `retrieval_context` across `LLMEngine` and `AssistantController`.

### 1.1. `voice_assistant.wiki.WikiRetriever` Mock
A new mock class `WikiRetriever` should be created to simulate the indexing and retrieval of local text chunks.
*   **Attributes**:
    *   `data_paths`: List of files/folders indexed.
    *   `kb_content`: Dictionary mapping query terms/keys to lists of mock text chunks.
    *   `default_chunks`: Fallback list of text chunks returned when no query match is found.
    *   `simulate_error`: Boolean flag to trigger lookup failures.
*   **Methods**:
    *   `retrieve(self, query: str, top_k: int = 2) -> list[str]`:
        *   Validates parameters (`query` must be a non-empty string, `top_k` must be a positive integer).
        *   Appends calls to `history.wiki_retrieve_calls`.
        *   If `simulate_error` is `True`, raises `RuntimeError`.
        *   Performs simple matching on `kb_content` keys. Returns the first matching entries up to `top_k`.
        *   Falls back to `default_chunks` if no matches are found.

### 1.2. Updating `LLMEngine`
Update the mock `LLMEngine.generate_response` method signature to accept `retrieval_context`.
*   **Signature**: `generate_response(self, prompt: str, context: list, retrieval_context: str = "") -> str`
*   **Audit**: Append `(prompt, context, retrieval_context)` to `history.llm_generate_calls` (replacing the previous two-tuple representation).
*   **Validation**: Verify that `retrieval_context` is a string (or raise `TypeError`).
*   **Simulation**: If `retrieval_context` is provided, append it to the mock response so that tests can assert that the generated answer incorporated the context.

### 1.3. Updating `AssistantController`
Update the coordinator loop in `AssistantController` to integrate RAG retrieval.
*   **Initialization**: Accept an optional `wiki_retriever` parameter (defaults to `None`). If not provided, initialize it to the default mock `WikiRetriever()` to preserve backward compatibility.
*   **`handle_input(self, input_type: str, content: str)`**:
    1.  Decodes input (transcribing via `STTEngine` if `input_type` is voice, or using directly if text).
    2.  If a prompt is obtained, queries `self.wiki_retriever.retrieve(prompt)`.
    3.  Wraps retrieval in a `try...except` block. If `WikiRetriever` raises an error, catch it and fall back to `retrieval_context = ""` gracefully (allowing the assistant to continue without context).
    4.  Calls `self.llm_engine.generate_response(prompt, self.context, retrieval_context=retrieval_context)`.

### 1.4. Mock Package Registration
Register the new `voice_assistant.wiki` module in the mock injection block:
```python
    va_wiki = ModuleType("voice_assistant.wiki")
    va_wiki.WikiRetriever = WikiRetriever
    sys.modules["voice_assistant.wiki"] = va_wiki
    va.wiki = va_wiki
```

---

## 2. Implementing R5 RAG Tests in `tests/test_rag.py`

The new test file `tests/test_rag.py` should implement Tiers 1-4 testing covering all requirements.

### 2.1. Tier 1: Happy-Path Coverage (5 cases)
1.  **`test_wiki_retriever_default_retrieve`**: Verifies that `WikiRetriever` starts successfully and returns the default simulated chunks for non-indexed queries.
2.  **`test_wiki_retriever_custom_retrieve`**: Verifies that custom context mapping works and returns matched queries' chunks up to `top_k`.
3.  **`test_llm_generate_with_retrieval_context`**: Verifies `LLMEngine.generate_response` records `retrieval_context` in its call history and formats the output accordingly.
4.  **`test_controller_integration_text_rag`**: Verifies that a text command triggers retrieval and correctly passes context to the LLM.
5.  **`test_controller_integration_voice_rag`**: Verifies that a voice command transcribes correctly, triggers retrieval, and forwards context to the LLM.

### 2.2. Tier 2: Boundary & Edge Cases (5 cases)
1.  **`test_wiki_retriever_invalid_top_k`**: Verifies `retrieve` raises `ValueError` when `top_k <= 0`, or `TypeError` for non-integer types.
2.  **`test_wiki_retriever_invalid_query_type`**: Verifies `retrieve` raises `TypeError` when the query is `None` or not a string.
3.  **`test_wiki_retriever_error_simulation`**: Verifies `retrieve` raises a `RuntimeError` when `simulate_error` is set to `True`.
4.  **`test_controller_rag_error_fallback`**: Verifies that if `WikiRetriever` raises an error during `handle_input`, the controller catches it, falls back to `retrieval_context=""` and calls LLM/TTS normally.
5.  **`test_llm_generate_invalid_retrieval_context_type`**: Verifies `LLMEngine.generate_response` raises `TypeError` if `retrieval_context` is not a string.

### 2.3. Tier 3: Cross-Feature Combinations (3 cases)
1.  **`test_rag_pipeline_with_volume_adjustment`**: Verifies that performing a RAG query after a volume configuration change uses the updated volume for speech output.
2.  **`test_rag_pipeline_with_interruption`**: Verifies that if a user interrupts the assistant while it is speaking a RAG-augmented response, speech is stopped immediately, a new retrieval is conducted for the new prompt, and the new response is generated.
3.  **`test_rag_multi_turn_history`**: Verifies that the complete conversation history is preserved across multiple turns while the new turn fetches fresh retrieval context.

### 2.4. Tier 4: Real-World Scenarios (2 cases)
1.  **`test_scenario_mvc_qa_session`**: Simulates a developer asking "What is the MVC pattern?". The retriever indexes and returns MVC-specific guidelines, the LLM uses them to explain MVC architecture, and the TTS speaks the response.
2.  **`test_scenario_solid_inquiry_offline_llm`**: Simulates querying about SOLID principles when the LLM server is offline (raises `ConnectionError`). The local retriever succeeds, but when the LLM fails, the system recovers by playing the local fallback audio.

---

## 3. Updating `tests/run_tests.py`

Currently, `tests/run_tests.py` uses `unittest.TestLoader.discover` with `pattern="test_tier*.py"`. To ensure the new `test_rag.py` is executed, we must update the discovery logic.
To avoid executing unrelated test scripts (e.g. experimental or challenger scripts), we should combine the discoveries of both patterns:
```python
    # Discover all tests matching 'test_tier*.py' and 'test_rag.py'
    loader = unittest.TestLoader()
    suite_tiers = loader.discover(start_dir=tests_dir, pattern="test_tier*.py")
    suite_rag = loader.discover(start_dir=tests_dir, pattern="test_rag.py")
    suite = unittest.TestSuite([suite_tiers, suite_rag])
```

---

## 4. Updating `TEST_INFRA.md`

We will update the testing documentation to describe R5 RAG tests.
*   **Section 2 (Feature Inventory)**: Add "6. Local Knowledge RAG Retrieval" which details the offline search index, parameter checks, and LLM prompt context injection.
*   **Section 3.2 (Test Files)**: Add `tests/test_rag.py` to the list of test files and explain its role in validating local knowledge base retrieval.
*   **Section 5 (Coverage Thresholds)**: Update the table to include RAG tests under Tiers 1-4, raising the total expected test counts.

---

# Proposed Code Changes

Below are the detailed code modifications.

### Proposed Code for `tests/mock_assistant.py`
```patch
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
        self.wiki_retrieve_calls = []

history = MockHistory()

def reset_history():
    history.tts_speak_calls.clear()
    history.tts_stop_calls.clear()
    history.stt_transcribe_calls.clear()
    history.llm_generate_calls.clear()
    history.controller_handle_input_calls.clear()
    history.controller_start_calls.clear()
    history.wiki_retrieve_calls.clear()
>>>>

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
        self.data_paths = data_paths if data_paths else []
        self.kb_content = {}
        self.default_chunks = ["Simulated local knowledge chunk 1", "Simulated local knowledge chunk 2"]
        self.simulate_error = False

    def retrieve(self, query: str, top_k: int = 2) -> list[str]:
        history.wiki_retrieve_calls.append((query, top_k))
        
        if self.simulate_error:
            raise RuntimeError("Simulated RAG database lookup failure")
        if query is None:
            raise TypeError("Query cannot be None")
        if not isinstance(query, str):
            raise TypeError("Query must be a string")
        if query == "":
            raise ValueError("Query cannot be empty")
        if top_k is None:
            raise TypeError("top_k cannot be None")
        if not isinstance(top_k, int):
            raise TypeError("top_k must be an integer")
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0")

        for k, v in self.kb_content.items():
            if k.lower() in query.lower():
                return v[:top_k]
                
        return self.default_chunks[:top_k]

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
        for item in context:
            if not isinstance(item, dict):
                raise TypeError("Context elements must be dictionaries")
        if retrieval_context is None:
            raise TypeError("Retrieval context cannot be None")
        if not isinstance(retrieval_context, str):
            raise TypeError("Retrieval context must be a string")

        if prompt in self.responses:
            return self.responses[prompt]
            
        if "hello" in prompt.lower():
            return "Hello! How can I help you?"
        if "dừng lại" in prompt.lower() or "stop" in prompt.lower():
            return "Stopping playback."
        
        if retrieval_context:
            return f"{self.default_response} using context: {retrieval_context} to: {prompt}"
        
        return f"{self.default_response} to: {prompt}"
>>>>

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
        self.wiki_retriever = wiki_retriever if wiki_retriever is not None else WikiRetriever()
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

        retrieval_context = ""
        if self.wiki_retriever:
            try:
                chunks = self.wiki_retriever.retrieve(prompt)
                retrieval_context = "\n".join(chunks)
            except Exception:
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
    va_wiki = ModuleType("voice_assistant.wiki")
    va_wiki.WikiRetriever = WikiRetriever
    sys.modules["voice_assistant.wiki"] = va_wiki
    va.wiki = va_wiki

    va_llm = ModuleType("voice_assistant.llm")
    va_llm.LLMEngine = LLMEngine
    sys.modules["voice_assistant.llm"] = va_llm
    va.llm = va_llm

    va_controller = ModuleType("voice_assistant.controller")
    va_controller.AssistantController = AssistantController
    sys.modules["voice_assistant.controller"] = va_controller
    va.controller = va_controller
>>>>
```

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

class TestRAG(unittest.TestCase):
    def setUp(self):
        mock_assistant.reset_history()
        config.DEFAULT_VOLUME = 0.5

    def tearDown(self):
        pass

    # ==========================================
    # Tier 1: Happy-Path Coverage (5 cases)
    # ==========================================
    def test_wiki_retriever_default_retrieve(self):
        """1. WikiRetriever returns default chunks when no query matches exist"""
        retriever = WikiRetriever()
        chunks = retriever.retrieve("Generic query", top_k=2)
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0], "Simulated local knowledge chunk 1")
        self.assertEqual(mock_assistant.history.wiki_retrieve_calls, [("Generic query", 2)])

    def test_wiki_retriever_custom_retrieve(self):
        """2. WikiRetriever returns custom context query mapping"""
        retriever = WikiRetriever()
        retriever.kb_content["solid"] = ["SOLID principle 1: Single Responsibility", "SOLID principle 2: Open-Closed"]
        chunks = retriever.retrieve("Tell me about SOLID design", top_k=1)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], "SOLID principle 1: Single Responsibility")

    def test_llm_generate_with_retrieval_context(self):
        """3. LLMEngine supports retrieval_context in generate_response"""
        llm = LLMEngine()
        response = llm.generate_response("Explain MVC", [], retrieval_context="MVC is Model-View-Controller")
        self.assertIn("MVC is Model-View-Controller", response)
        self.assertEqual(mock_assistant.history.llm_generate_calls[0][2], "MVC is Model-View-Controller")

    def test_controller_integration_text_rag(self):
        """4. AssistantController text pipeline retrieves and passes context to LLM"""
        retriever = WikiRetriever()
        retriever.kb_content["mvc"] = ["Controller manages flow"]
        llm = LLMEngine()
        tts = TTSEngine()
        controller = AssistantController(tts_engine=tts, llm_engine=llm, wiki_retriever=retriever)

        controller.handle_input("text", "Explain mvc pattern")
        self.assertEqual(len(mock_assistant.history.wiki_retrieve_calls), 1)
        self.assertEqual(mock_assistant.history.llm_generate_calls[0][2], "Controller manages flow")

    def test_controller_integration_voice_rag(self):
        """5. AssistantController voice pipeline transcribes, retrieves, and passes context to LLM"""
        stt = STTEngine()
        stt.transcriptions["query.wav"] = "What are SOLID rules?"
        
        retriever = WikiRetriever()
        retriever.kb_content["solid"] = ["L stands for Liskov Substitution"]
        
        llm = LLMEngine()
        tts = TTSEngine()
        controller = AssistantController(tts_engine=tts, stt_engine=stt, llm_engine=llm, wiki_retriever=retriever)

        controller.handle_input("voice", "query.wav")
        self.assertEqual(mock_assistant.history.stt_transcribe_calls, ["query.wav"])
        self.assertEqual(mock_assistant.history.wiki_retrieve_calls[0][0], "What are SOLID rules?")
        self.assertEqual(mock_assistant.history.llm_generate_calls[0][2], "L stands for Liskov Substitution")


    # ==========================================
    # Tier 2: Boundary & Edge Cases (5 cases)
    # ==========================================
    def test_wiki_retriever_invalid_top_k(self):
        """1. WikiRetriever.retrieve raises errors on invalid top_k values"""
        retriever = WikiRetriever()
        with self.assertRaises(ValueError):
            retriever.retrieve("query", top_k=0)
        with self.assertRaises(ValueError):
            retriever.retrieve("query", top_k=-5)
        with self.assertRaises(TypeError):
            retriever.retrieve("query", top_k="two")
        with self.assertRaises(TypeError):
            retriever.retrieve("query", top_k=None)

    def test_wiki_retriever_invalid_query_type(self):
        """2. WikiRetriever.retrieve raises errors on invalid query inputs"""
        retriever = WikiRetriever()
        with self.assertRaises(TypeError):
            retriever.retrieve(None)
        with self.assertRaises(TypeError):
            retriever.retrieve(12345)
        with self.assertRaises(ValueError):
            retriever.retrieve("")

    def test_wiki_retriever_error_simulation(self):
        """3. WikiRetriever raises RuntimeError when simulate_error is set"""
        retriever = WikiRetriever()
        retriever.simulate_error = True
        with self.assertRaises(RuntimeError):
            retriever.retrieve("Testing error")

    def test_controller_rag_error_fallback(self):
        """4. Controller falls back gracefully (empty retrieval_context) when retriever fails"""
        retriever = WikiRetriever()
        retriever.simulate_error = True
        llm = LLMEngine()
        tts = TTSEngine()
        controller = AssistantController(tts_engine=tts, llm_engine=llm, wiki_retriever=retriever)

        # Act - Should not raise RuntimeError
        controller.handle_input("text", "Testing error safety")
        
        # Verify LLM call went through with empty retrieval context
        self.assertEqual(mock_assistant.history.llm_generate_calls[0][2], "")
        self.assertTrue(tts.is_speaking())
        tts.stop()

    def test_llm_generate_invalid_retrieval_context_type(self):
        """5. LLMEngine generate_response validates retrieval_context type"""
        llm = LLMEngine()
        with self.assertRaises(TypeError):
            llm.generate_response("prompt", [], retrieval_context=123)
        with self.assertRaises(TypeError):
            llm.generate_response("prompt", [], retrieval_context=None)


    # ==========================================
    # Tier 3: Cross-Feature Combinations (3 cases)
    # ==========================================
    def test_rag_pipeline_with_volume_adjustment(self):
        """1. RAG retrieval pipeline works in tandem with volume configuration updates"""
        retriever = WikiRetriever()
        llm = LLMEngine()
        tts = TTSEngine()
        controller = AssistantController(tts_engine=tts, llm_engine=llm, wiki_retriever=retriever)

        config.DEFAULT_VOLUME = 0.35
        controller.handle_input("text", "Volume + RAG query")
        
        # Verify speech volume is set to 0.35
        self.assertEqual(mock_assistant.history.tts_speak_calls[0][1], 0.35)
        tts.stop()

    def test_rag_pipeline_with_interruption(self):
        """2. New text input halts RAG speech playback and issues a new retrieval & generation"""
        retriever = WikiRetriever()
        retriever.kb_content["query1"] = ["Context one"]
        retriever.kb_content["query2"] = ["Context two"]
        llm = LLMEngine()
        tts = TTSEngine()
        controller = AssistantController(tts_engine=tts, llm_engine=llm, wiki_retriever=retriever)

        # 1. First input
        controller.handle_input("text", "query1")
        self.assertTrue(tts.is_speaking())
        
        # 2. Interruption with new query
        controller.handle_input("text", "query2")
        
        # Verify interruption occurred
        self.assertTrue(controller.interrupted_flag)
        self.assertEqual(len(mock_assistant.history.tts_stop_calls), 1)
        # Verify second query was retrieved and generated
        self.assertEqual(mock_assistant.history.wiki_retrieve_calls[1][0], "query2")
        self.assertEqual(mock_assistant.history.llm_generate_calls[1][2], "Context two")
        tts.stop()

    def test_rag_multi_turn_history(self):
        """3. Multi-turn conversation history is maintained while fetching new retrieval context per turn"""
        retriever = WikiRetriever()
        retriever.kb_content["turn1"] = ["Information one"]
        retriever.kb_content["turn2"] = ["Information two"]
        llm = LLMEngine()
        tts = TTSEngine()
        controller = AssistantController(tts_engine=tts, llm_engine=llm, wiki_retriever=retriever)

        # Turn 1
        controller.handle_input("text", "turn1")
        self.assertEqual(len(controller.context), 2)
        
        # Turn 2
        controller.handle_input("text", "turn2")
        self.assertEqual(len(controller.context), 4)
        
        # Verify the context history was correctly forwarded in the second LLM call
        passed_history = mock_assistant.history.llm_generate_calls[1][1]
        self.assertEqual(passed_history[0]["role"], "user")
        self.assertEqual(passed_history[0]["content"], "turn1")
        self.assertEqual(mock_assistant.history.llm_generate_calls[1][2], "Information two")
        tts.stop()


    # ==========================================
    # Tier 4: Real-World Scenarios (2 cases)
    # ==========================================
    def test_scenario_mvc_qa_session(self):
        """Scenario: Developer MVC QA Session
        User asks "What is MVC?".
        Retriever fetches MVC guidelines.
        LLM outputs RAG-augmented response.
        TTS speaks the response.
        """
        retriever = WikiRetriever()
        retriever.kb_content["what is mvc"] = ["MVC stands for Model-View-Controller. Model manages state."]
        llm = LLMEngine()
        tts = TTSEngine()
        controller = AssistantController(tts_engine=tts, llm_engine=llm, wiki_retriever=retriever)

        controller.handle_input("text", "What is MVC?")

        # Assertions
        self.assertEqual(mock_assistant.history.wiki_retrieve_calls[0][0], "What is MVC?")
        self.assertEqual(mock_assistant.history.llm_generate_calls[0][2], "MVC stands for Model-View-Controller. Model manages state.")
        self.assertIn("MVC stands for Model-View-Controller", mock_assistant.history.tts_speak_calls[0][0])
        tts.stop()

    def test_scenario_solid_inquiry_offline_llm(self):
        """Scenario: SOLID inquiry with offline LLM error
        User queries "Explain SOLID".
        Retriever fetches context successfully.
        LLM fails due to connection error (simulated offline).
        Controller throws ConnectionError, test catches it and falls back to local pre-recorded error message.
        """
        retriever = WikiRetriever()
        retriever.kb_content["solid"] = ["S stands for Single Responsibility"]
        llm = LLMEngine()
        llm.simulate_offline = True
        tts = TTSEngine()
        controller = AssistantController(tts_engine=tts, llm_engine=llm, wiki_retriever=retriever)

        fallback_played = False
        try:
            controller.handle_input("text", "Explain solid rules")
        except ConnectionError:
            tts.speak("Connection failed. Showing local offline help for SOLID.", volume=0.5)
            fallback_played = True

        self.assertTrue(fallback_played)
        self.assertEqual(mock_assistant.history.wiki_retrieve_calls[0][0], "Explain solid rules")
        self.assertEqual(mock_assistant.history.tts_speak_calls[0][0], "Connection failed. Showing local offline help for SOLID.")
        tts.stop()

if __name__ == "__main__":
    unittest.main()
```

### Proposed Code for `tests/run_tests.py`
```patch
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
    suite_tiers = loader.discover(start_dir=tests_dir, pattern="test_tier*.py")
    suite_rag = loader.discover(start_dir=tests_dir, pattern="test_rag.py")
    suite = unittest.TestSuite([suite_tiers, suite_rag])
    
    # Run tests using custom text runner
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
>>>>
```

### Proposed Documentation Updates for `TEST_INFRA.md`
```patch
<<<<
2.  **Speech-to-Text (STT)**:
    *   Accurate local transcription via `transcribe(audio_path_or_data)`.
    *   Support for local audio files and binary input data.
    *   Robust handling of missing, corrupt, or unsupported formats.
3.  **Large Language Model (LLM)**:
    *   Local offline instruction response generation.
    *   Context history tracking through multi-turn conversations.
    *   Consistent handling of invalid input states and network mock interruptions.
4.  **Playback Interruption Control**:
====
2.  **Speech-to-Text (STT)**:
    *   Accurate local transcription via `transcribe(audio_path_or_data)`.
    *   Support for local audio files and binary input data.
    *   Robust handling of missing, corrupt, or unsupported formats.
3.  **Large Language Model (LLM)**:
    *   Local offline instruction response generation.
    *   Context history tracking through multi-turn conversations.
    *   Consistent handling of invalid input states and network mock interruptions.
    *   Acceptance of optional retrieval context to ground output.
4.  **Local Knowledge Base & RAG Retrieval**:
    *   Retrieval of relevant text blocks via `WikiRetriever.retrieve(query, top_k)`.
    *   Parameter checking and validation.
    *   Graceful fallback handling (continuing LLM generation without context if retrieval fails).
5.  **Playback Interruption Control**:
>>>>

<<<<
### 3.1 Test Runner (`tests/run_tests.py`)
*   **Discovery**: Automatically scans the `tests/` directory for files matching `test_tier*.py`.
*   **Environment Preparation**: Automatically injects `MOCK_ENGINES=1` into `os.environ` to enable mocked modes when running in decoupled or CI/CD pipelines.
*   **Execution**: Discovers all 60 tests and runs them sequentially.
*   **Aggregation & Reporting**: Collects test results (Run count, Passed, Failed, Errors), prints a formatted stdout summary, and returns exit code `0` on success or `1` on failure.

### 3.2 Test Files
*   `tests/test_tier1_coverage.py`: Happy-path feature verification.
*   `tests/test_tier2_boundaries.py`: Edge cases, negative inputs, and boundaries.
*   `tests/test_tier3_combinations.py`: Cross-feature integration pipelines.
*   `tests/test_tier4_scenarios.py`: Realistic end-user workflow validation.

### 3.3 Mocking and Patching Mechanism (`tests/mock_assistant.py`)
*   **Dynamic sys.modules Injection**: If `MOCK_ENGINES=1` is set, or if the `voice_assistant` package cannot be imported on disk (for example, in early development phases), `mock_assistant` injects mock versions of `voice_assistant`, `voice_assistant.tts`, `voice_assistant.stt`, `voice_assistant.llm`, `voice_assistant.controller`, and `voice_assistant.config` into the global `sys.modules` table.
====
### 3.1 Test Runner (`tests/run_tests.py`)
*   **Discovery**: Automatically scans the `tests/` directory for files matching `test_tier*.py` and `test_rag.py`.
*   **Environment Preparation**: Automatically injects `MOCK_ENGINES=1` into `os.environ` to enable mocked modes when running in decoupled or CI/CD pipelines.
*   **Execution**: Discovers all tests and runs them sequentially.
*   **Aggregation & Reporting**: Collects test results (Run count, Passed, Failed, Errors), prints a formatted stdout summary, and returns exit code `0` on success or `1` on failure.

### 3.2 Test Files
*   `tests/test_tier1_coverage.py`: Happy-path feature verification.
*   `tests/test_tier2_boundaries.py`: Edge cases, negative inputs, and boundaries.
*   `tests/test_tier3_combinations.py`: Cross-feature integration pipelines.
*   `tests/test_tier4_scenarios.py`: Realistic end-user workflow validation.
*   `tests/test_rag.py`: Verifies local knowledge retrieval, error handling, parameter constraints, and RAG E2E integration pipelines.

### 3.3 Mocking and Patching Mechanism (`tests/mock_assistant.py`)
*   **Dynamic sys.modules Injection**: If `MOCK_ENGINES=1` is set, or if the `voice_assistant` package cannot be imported on disk (for example, in early development phases), `mock_assistant` injects mock versions of `voice_assistant`, `voice_assistant.tts`, `voice_assistant.stt`, `voice_assistant.llm`, `voice_assistant.wiki`, `voice_assistant.controller`, and `voice_assistant.config` into the global `sys.modules` table.
>>>>

<<<<
| Test Tier | Focus Area | Minimum Threshold | Implemented | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1** | Happy-Path Coverage (5 per feature) | $\ge$ 25 cases | 25 cases | **Passed** |
| **Tier 2** | Boundary & Edge Cases (5 per feature) | $\ge$ 25 cases | 25 cases | **Passed** |
| **Tier 3** | Cross-Feature Combinations | $\ge$ 5 cases | 5 cases | **Passed** |
| **Tier 4** | Real-World Workflow Scenarios | $\ge$ 5 cases | 5 cases | **Passed** |
| **Total** | **Comprehensive E2E Suite** | **$\ge$ 60 cases** | **60 cases** | **Passed** |
====
| Test Tier | Focus Area | Minimum Threshold | Implemented | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1** | Happy-Path Coverage | $\ge$ 30 cases | 30 cases | **Passed** |
| **Tier 2** | Boundary & Edge Cases | $\ge$ 30 cases | 30 cases | **Passed** |
| **Tier 3** | Cross-Feature Combinations | $\ge$ 8 cases | 8 cases | **Passed** |
| **Tier 4** | Real-World Workflow Scenarios | $\ge$ 7 cases | 7 cases | **Passed** |
| **Total** | **Comprehensive E2E Suite** | **$\ge$ 75 cases** | **75 cases** | **Passed** |
>>>>
```
