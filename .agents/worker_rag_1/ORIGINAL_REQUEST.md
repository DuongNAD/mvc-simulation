## 2026-06-21T01:15:25Z

You are a Developer/Worker Agent. Your working directory is e:\test\mvc-simulation\.agents\worker_rag_1.
Your task is to implement R5 RAG validation changes in the test suite and update documentation.
Follow these steps:

1. Update `tests/mock_assistant.py`:
   - Add a mock `WikiRetriever` class with contract: `retrieve(self, query: str, top_k: int = 2) -> list[str]`. It must be genuine: if `excel_output.txt`, `script.txt`, or `sample_sheet.csv` exist in the workspace, it should inspect them to perform basic keyword/substring searches, and return matching chunks (falling back to a default list of chunks if no matches are found).
   - Track calls in `history.wiki_retrieve_calls` (query and top_k). Update `MockHistory` and `reset_history()`.
   - Update `LLMEngine.generate_response` mock signature: `generate_response(self, prompt: str, context: list, retrieval_context: str = "") -> str`. Track `retrieval_context` in `history.llm_generate_calls`. Include the retrieval context in the mock response if present.
   - Update `AssistantController` mock: take optional `wiki_retriever` parameter (default `None`, instantiates mock `WikiRetriever`). In `handle_input`, call `wiki_retriever.retrieve(prompt)`. Format retrieved chunks into a single `retrieval_context` string. Wrap this in try/except to gracefully fall back to `retrieval_context = ""` on error. Pass it to `LLMEngine.generate_response`.
   - If `should_mock` is True, inject `voice_assistant.wiki` containing `WikiRetriever` mock class into `sys.modules`.

2. Create `tests/test_rag.py` using Python's standard `unittest` library:
   - Tier 1: Happy paths. At least 5 test cases verifying: (a) default wiki retriever retrieval, (b) retrieval respecting `top_k`, (c) indexing/retrieving SOLID chunks from `excel_output.txt`, (d) indexing/retrieving chunks from `script.txt`, (e) controller RAG integration happy path.
   - Tier 2: Boundary/Edge cases. At least 5 test cases: (a) empty query ValueError, (b) query with special characters handling, (c) missing/non-existent documents handling, (d) empty document handling, (e) retrieving more chunks than exist.
   - Tier 3: Combinations. At least 3 test cases: (a) RAG context integration into LLM chat, (b) RAG retrieval failure fallback in controller, (c) STT to RAG to LLM to TTS pipeline.
   - Tier 4: Real-world scenario. At least 2 test cases, including a scenario where the user asks "Explain Model" in Vietnamese, retriever indexes `sample_sheet.csv` to retrieve "Doctor.java" descriptions, feeds it to the LLM, and speaks the response (verifying default volume).

3. Update `tests/run_tests.py`:
   - Adjust the test loader discovery to run both `test_tier*.py` and `test_rag.py` test suites.

4. Update `TEST_INFRA.md`:
   - Document RAG feature inventory, mock details, scenarios, and update the coverage count table showing 75 total tests (60 original + 15 new RAG tests).

5. Verification:
   - Run the full test runner using Python: `py tests/run_tests.py` (ensure you load the mock engines). Verify that all 75 tests pass with exit code 0.
   - Capture the test runner execution output.

6. Update `TEST_READY.md`:
   - Revise the `TEST_READY.md` file at the project root with a summary of the 75 test cases and paste the stdout log output of the successful run.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Reply with your handoff report and status when done.
