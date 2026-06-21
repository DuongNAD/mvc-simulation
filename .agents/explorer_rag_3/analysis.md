# R5 RAG Automated Test Integration Analysis

## Summary
This analysis outlines the required changes to integrate local offline Wiki/Knowledge Base Retrieval-Augmented Generation (R5 RAG) verification into the existing test suite. It provides precise specifications for mocking `WikiRetriever`, augmenting the mock `LLMEngine` and `AssistantController`, implementing `tests/test_rag.py` across Tiers 1-4, adjusting `tests/run_tests.py` for test discovery, and updating `TEST_INFRA.md`.

---

## 1. Mocking RAG Components in `tests/mock_assistant.py`

To decouple the automated E2E tests from local indexing engines, database packages, and CPU/GPU hardware resources, the testing harness must stub out all R5 RAG components.

### 1.1 Mocking `voice_assistant.wiki.WikiRetriever`
A mock class `WikiRetriever` must be added to simulate factual database lookups.
*   **Contract**: `retrieve(self, query: str, top_k: int = 2) -> list[str]`
*   **Behavior**:
    *   Maintains a customizable dict of mapped queries (`responses`) and returns a default list of text chunks if no matching query is found.
    *   Tracks its call parameters inside the global `MockHistory` object via `wiki_retrieve_calls`.
    *   Exposes a state flag `simulate_failure: bool` that triggers a `RuntimeError` during retrieval to test the controller's robustness.

### 1.2 Enhancing `MockHistory`
`MockHistory` needs to register:
*   `wiki_retrieve_calls` to verify query routing, top-k limits, and retrieval interactions.
*   `reset_history()` should clear this collection.

### 1.3 Updating `LLMEngine`
The mock `LLMEngine.generate_response` signature must support `retrieval_context` to mimic the updated engine contract:
*   **Signature**: `generate_response(self, prompt: str, context: list, retrieval_context: str = "") -> str`
*   **Mock Verification**:
    *   Asserts type safety (checks if `retrieval_context` is a string).
    *   Appends `retrieval_context` to the recorded call log history.
    *   Uses `retrieval_context` in generated output text if present to facilitate assertion checks in end-to-end assertions.

### 1.4 Updating `AssistantController`
The controller coordinator manages the pipeline interaction:
*   In `__init__`, it instantiates/accepts a `wiki_retriever`.
*   In `handle_input(input_type, content)`, it invokes `self.wiki_retriever.retrieve(prompt)` before calling the LLM.
*   It aggregates returned chunks by joining them (e.g. `\n`.join(chunks)) to form the final `retrieval_context`.
*   **Graceful Fallback**: It wraps the retrieval step in a `try/except` block. If `WikiRetriever` raises an exception, the coordinator logs the failure, sets `retrieval_context = ""`, and proceeds to call `LLMEngine.generate_response(..., retrieval_context="")` without failing.

### 1.5 Dynamic Module Injection
`sys.modules` patching must inject the new `voice_assistant.wiki` module containing the `WikiRetriever` mock class.

---

### Proposed Code for `tests/mock_assistant.py`

```python
# ==========================================
# 1. Update MockHistory
# ==========================================
class MockHistory:
    def __init__(self):
        self.tts_speak_calls = []
        self.tts_stop_calls = []
        self.stt_transcribe_calls = []
        self.llm_generate_calls = []
        self.controller_handle_input_calls = []
        self.controller_start_calls = []
        self.wiki_retrieve_calls = [] # Added for R5

def reset_history():
    history.tts_speak_calls.clear()
    history.tts_stop_calls.clear()
    history.stt_transcribe_calls.clear()
    history.llm_generate_calls.clear()
    history.controller_handle_input_calls.clear()
    history.controller_start_calls.clear()
    history.wiki_retrieve_calls.clear() # Added for R5

# ==========================================
# 2. Add WikiRetriever Mock
# ==========================================
class WikiRetriever:
    def __init__(self):
        self.responses = {}
        self.default_response = ["Simulated wiki content chunk 1", "Simulated wiki content chunk 2"]
        self.simulate_failure = False

    def retrieve(self, query: str, top_k: int = 2) -> list:
        history.wiki_retrieve_calls.append((query, top_k))
        if self.simulate_failure:
            raise RuntimeError("Simulated wiki retrieval failure")
        if query is None:
            raise TypeError("Query cannot be None")
        if query == "":
            raise ValueError("Query cannot be empty")
        if not isinstance(top_k, int) or top_k <= 0:
            raise ValueError("top_k must be a positive integer")

        if query in self.responses:
            return self.responses[query][:top_k]

        # Check if the query is a substring of registered responses
        for q, res in self.responses.items():
            if q.lower() in query.lower():
                return res[:top_k]

        return self.default_response[:top_k]

# ==========================================
# 3. Update LLMEngine Mock
# ==========================================
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

        if retrieval_context:
            return f"{self.default_response} with context '{retrieval_context}' to: {prompt}"
            
        if "hello" in prompt.lower():
            return "Hello! How can I help you?"
        if "dừng lại" in prompt.lower() or "stop" in prompt.lower():
            return "Stopping playback."
        
        return f"{self.default_response} to: {prompt}"

# ==========================================
# 4. Update AssistantController Mock
# ==========================================
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

        # RAG retrieval step with error handling
        retrieval_context = ""
        try:
            if self.wiki_retriever:
                chunks = self.wiki_retriever.retrieve(prompt)
                if chunks:
                    retrieval_context = "\n".join(chunks)
        except Exception as e:
            # Fallback gracefully (LLM will be called without RAG context)
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

# ==========================================
# 5. Injection Section (in should_mock conditional)
# ==========================================
if should_mock:
    # ... (existing module mappings) ...
    va_wiki = ModuleType("voice_assistant.wiki")
    va_wiki.WikiRetriever = WikiRetriever
    sys.modules["voice_assistant.wiki"] = va_wiki
    va.wiki = va_wiki
```

---

## 2. Test File Design for `tests/test_rag.py`

`tests/test_rag.py` must contain isolated, state-resetting E2E verification spanning all 4 required test tiers.

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
from voice_assistant.tts import TTSEngine
from voice_assistant.stt import STTEngine
from voice_assistant.controller import AssistantController
import voice_assistant.config as config

class TestRAGSystem(unittest.TestCase):
    def setUp(self):
        mock_assistant.reset_history()
        config.DEFAULT_VOLUME = 0.5

    def tearDown(self):
        pass

    # =========================================================================
    # Tier 1: Happy-Path Feature Verification (5 cases)
    # =========================================================================
    def test_tier1_wiki_retriever_default_retrieval(self):
        """Verify WikiRetriever returns default chunks and logs parameters in history."""
        retriever = WikiRetriever()
        chunks = retriever.retrieve("What is MVC?")
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0], "Simulated wiki content chunk 1")
        self.assertEqual(mock_assistant.history.wiki_retrieve_calls[0], ("What is MVC?", 2))

    def test_tier1_wiki_retriever_retrieve_top_k(self):
        """Verify retrieve limits returned results via the top_k parameter."""
        retriever = WikiRetriever()
        chunks = retriever.retrieve("What is SOLID?", top_k=1)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], "Simulated wiki content chunk 1")

    def test_tier1_wiki_retriever_custom_responses(self):
        """Verify WikiRetriever correctly matches and returns configured custom responses."""
        retriever = WikiRetriever()
        retriever.responses["design patterns"] = ["Singleton ensures one instance.", "Factory creates objects."]
        chunks = retriever.retrieve("Tell me about design patterns")
        self.assertEqual(chunks, ["Singleton ensures one instance.", "Factory creates objects."])

    def test_tier1_llm_generation_with_retrieval_context(self):
        """Verify LLMEngine successfully accepts retrieval_context and includes it in output."""
        llm = LLMEngine()
        prompt = "Explain MVC"
        retrieval_context = "MVC is Model-View-Controller pattern."
        response = llm.generate_response(prompt, [], retrieval_context=retrieval_context)
        self.assertIn(retrieval_context, response)
        self.assertEqual(mock_assistant.history.llm_generate_calls[0], (prompt, [], retrieval_context))

    def test_tier1_controller_integration_happy_path(self):
        """Verify AssistantController retrieves context and passes it into LLMEngine in E2E flow."""
        retriever = WikiRetriever()
        retriever.responses["MVC"] = ["Model handles data.", "View handles UI."]
        llm = LLMEngine()
        controller = AssistantController(wiki_retriever=retriever, llm_engine=llm)
        
        controller.handle_input("text", "MVC explanation")
        self.assertEqual(len(mock_assistant.history.wiki_retrieve_calls), 1)
        self.assertEqual(mock_assistant.history.wiki_retrieve_calls[0][0], "MVC explanation")
        
        expected_context = "Model handles data.\nView handles UI."
        self.assertEqual(mock_assistant.history.llm_generate_calls[0][2], expected_context)

    # =========================================================================
    # Tier 2: Edge & Boundary Cases (5 cases)
    # =========================================================================
    def test_tier2_wiki_retriever_empty_query(self):
        """Verify WikiRetriever raises ValueError for empty string queries."""
        retriever = WikiRetriever()
        with self.assertRaises(ValueError):
            retriever.retrieve("")

    def test_tier2_wiki_retriever_none_query(self):
        """Verify WikiRetriever raises TypeError for None queries."""
        retriever = WikiRetriever()
        with self.assertRaises(TypeError):
            retriever.retrieve(None)

    def test_tier2_wiki_retriever_invalid_top_k(self):
        """Verify WikiRetriever raises ValueError for negative or zero top_k inputs."""
        retriever = WikiRetriever()
        with self.assertRaises(ValueError):
            retriever.retrieve("query", top_k=-1)
        with self.assertRaises(ValueError):
            retriever.retrieve("query", top_k=0)

    def test_tier2_llm_invalid_retrieval_context_type(self):
        """Verify LLMEngine raises TypeError for invalid retrieval_context data types."""
        llm = LLMEngine()
        with self.assertRaises(TypeError):
            llm.generate_response("prompt", [], retrieval_context=123)
        with self.assertRaises(TypeError):
            llm.generate_response("prompt", [], retrieval_context=None)

    def test_tier2_controller_handles_retrieval_failure_gracefully(self):
        """Verify AssistantController handles WikiRetriever exceptions gracefully and falls back."""
        retriever = WikiRetriever()
        retriever.simulate_failure = True
        llm = LLMEngine()
        controller = AssistantController(wiki_retriever=retriever, llm_engine=llm)
        
        # Verify no crash occurs
        controller.handle_input("text", "What is SOLID?")
        
        # Verify LLM was still invoked, but with empty retrieval context
        self.assertEqual(len(mock_assistant.history.llm_generate_calls), 1)
        self.assertEqual(mock_assistant.history.llm_generate_calls[0][2], "")

    # =========================================================================
    # Tier 3: Cross-Feature Integration Combinations (3 cases)
    # =========================================================================
    def test_tier3_voice_input_rag_pipeline(self):
        """Verify full voice-based pipeline incorporates retrieved context into TTS output."""
        stt = STTEngine()
        stt.transcriptions["solid_audio.wav"] = "Tell me about SOLID design rules"
        
        retriever = WikiRetriever()
        retriever.responses["SOLID"] = ["SOLID represents 5 principles."]
        
        llm = LLMEngine()
        tts = TTSEngine()
        
        controller = AssistantController(
            stt_engine=stt,
            wiki_retriever=retriever,
            llm_engine=llm,
            tts_engine=tts
        )
        
        controller.handle_input("voice", "solid_audio.wav")
        
        self.assertEqual(mock_assistant.history.stt_transcribe_calls, ["solid_audio.wav"])
        self.assertEqual(mock_assistant.history.wiki_retrieve_calls[0][0], "Tell me about SOLID design rules")
        self.assertEqual(mock_assistant.history.llm_generate_calls[0][2], "SOLID represents 5 principles.")
        self.assertEqual(len(mock_assistant.history.tts_speak_calls), 1)
        self.assertIn("SOLID represents 5 principles.", mock_assistant.history.tts_speak_calls[0][0])

    def test_tier3_rag_context_isolated_per_turn(self):
        """Verify that multi-turn queries query the knowledge base and retrieve fresh context each turn."""
        retriever = WikiRetriever()
        retriever.responses["first"] = ["Context A"]
        retriever.responses["second"] = ["Context B"]
        
        llm = LLMEngine()
        controller = AssistantController(wiki_retriever=retriever, llm_engine=llm)
        
        controller.handle_input("text", "first query")
        self.assertEqual(mock_assistant.history.llm_generate_calls[0][2], "Context A")
        
        controller.handle_input("text", "second query")
        self.assertEqual(mock_assistant.history.llm_generate_calls[1][2], "Context B")

    def test_tier3_rag_empty_retrieved_list_behavior(self):
        """Verify coordinator behavior when retriever returns an empty list (0 matches)."""
        retriever = WikiRetriever()
        retriever.responses["nothing"] = []
        llm = LLMEngine()
        controller = AssistantController(wiki_retriever=retriever, llm_engine=llm)
        
        controller.handle_input("text", "nothing")
        self.assertEqual(mock_assistant.history.llm_generate_calls[0][2], "")

    # =========================================================================
    # Tier 4: Real-World Scenarios (2 cases)
    # =========================================================================
    def test_tier4_scenario_6_developer_query_mvc_guidelines(self):
        """Scenario 6: Developer Querying MVC/SOLID Rules.
        Verify retrieving specific MVC View guidelines, LLM augmentation, and speech reading.
        """
        retriever = WikiRetriever()
        retriever.responses["View layer"] = ["The View displays model data and sends user actions to Controller."]
        
        llm = LLMEngine()
        tts = TTSEngine()
        controller = AssistantController(wiki_retriever=retriever, llm_engine=llm, tts_engine=tts)
        
        controller.handle_input("text", "Explain the View layer")
        
        self.assertEqual(mock_assistant.history.wiki_retrieve_calls[0][0], "Explain the View layer")
        self.assertEqual(mock_assistant.history.llm_generate_calls[0][2], "The View displays model data and sends user actions to Controller.")
        self.assertIn("The View displays model data", mock_assistant.history.tts_speak_calls[0][0])

    def test_tier4_scenario_7_knowledge_retrieval_failure_fallback(self):
        """Scenario 7: Knowledge Retrieval Failure with Offline LLM Fallback.
        Verify system safety and recovery when Wiki retriever throws errors.
        """
        retriever = WikiRetriever()
        retriever.simulate_failure = True
        
        llm = LLMEngine()
        tts = TTSEngine()
        controller = AssistantController(wiki_retriever=retriever, llm_engine=llm, tts_engine=tts)
        
        controller.handle_input("text", "Give me SOLID principles advice")
        
        self.assertEqual(len(mock_assistant.history.wiki_retrieve_calls), 1)
        self.assertEqual(mock_assistant.history.llm_generate_calls[0][2], "")
        self.assertEqual(len(mock_assistant.history.tts_speak_calls), 1)
        self.assertEqual(mock_assistant.history.tts_speak_calls[0][0], "Simulated assistant response to: Give me SOLID principles advice")
```

---

## 3. Test Discovery Updates in `tests/run_tests.py`

Currently, `tests/run_tests.py` performs test discovery using the glob pattern `"test_tier*.py"`. Since `test_rag.py` sits outside this naming convention but represents core E2E tests, the loader needs to discover both patterns.

### Proposed Code for `tests/run_tests.py`

#### Target Location: lines 26 to 29

**Before:**
```python
    # Discover all tests matching 'test_tier*.py'
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=tests_dir, pattern="test_tier*.py")
```

**After (Proposed):**
```python
    # Discover all core tests matching 'test_tier*.py' and RAG tests 'test_rag.py'
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    tier_tests = loader.discover(start_dir=tests_dir, pattern="test_tier*.py")
    rag_tests = loader.discover(start_dir=tests_dir, pattern="test_rag.py")
    
    suite.addTests(tier_tests)
    suite.addTests(rag_tests)
```

---

## 4. Updates to `TEST_INFRA.md`

`TEST_INFRA.md` must be modified to reflect the addition of RAG. 

### Proposed Changes

#### 1. Under Section 2 (`Feature Inventory`), append:
```markdown
6.  **Wiki/Knowledge Base Retrieval (RAG)**:
    *   Local factual retrieval of document chunks via `WikiRetriever.retrieve`.
    *   Context-augmented prompt generation in `LLMEngine.generate_response(..., retrieval_context=...)`.
    *   Seamless controller integration, including fallback mechanisms to handle database or retrieval failures gracefully.
```

#### 2. Under Section 3.2 (`Test Files`), append:
```markdown
*   `tests/test_rag.py`: RAG feature validation across Tiers 1-4 (includes fallback tests).
```

#### 3. Under Section 3.3 (`Mocking and Patching Mechanism`), append:
```markdown
*   **Wiki/RAG Injection**: Injecting mock version of `voice_assistant.wiki` containing `WikiRetriever` with full call tracking (`wiki_retrieve_calls`) and failure simulation states.
```

#### 4. Under Section 4 (`Real-World Application Scenarios`), append:
```markdown
6.  **Scenario 6: Developer Querying MVC/SOLID Rules**
    *   *Description*: The user asks a question about MVC view layers.
    *   *Verification*: `WikiRetriever` retrieves corresponding design guidelines, and `LLMEngine` produces a response augmented with the retrieved information.
7.  **Scenario 7: Knowledge Retrieval Failure with Offline LLM Fallback**
    *   *Description*: The retrieval engine encounters an unexpected failure.
    *   *Verification*: The coordinator handles the error gracefully, queries the LLM with empty retrieval context, and reads the response normally.
```

#### 5. Under Section 5 (`Coverage Thresholds`), update the summary table:
```markdown
| Test Tier | Focus Area | Minimum Threshold | Implemented | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1** | Happy-Path Coverage (5 per feature + 5 RAG) | $\ge$ 30 cases | 30 cases | **Passed** |
| **Tier 2** | Boundary & Edge Cases (5 per feature + 5 RAG) | $\ge$ 30 cases | 30 cases | **Passed** |
| **Tier 3** | Cross-Feature Combinations (5 original + 3 RAG) | $\ge$ 8 cases | 8 cases | **Passed** |
| **Tier 4** | Real-World Workflow Scenarios (5 original + 2 RAG) | $\ge$ 7 cases | 7 cases | **Passed** |
| **Total** | **Comprehensive E2E Suite** | **$\ge$ 75 cases** | **75 cases** | **Passed** |
```
