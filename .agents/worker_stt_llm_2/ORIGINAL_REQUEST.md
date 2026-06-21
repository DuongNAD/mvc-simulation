## 2026-06-21T01:16:45Z
You are the STT & LLM RAG Worker for Milestone 2.
Your working directory is e:\test\mvc-simulation\.agents\worker_stt_llm_2.

OBJECTIVE:
Implement the local Wiki RAG system in voice_assistant/wiki.py, update voice_assistant/llm.py to integrate retrieval context and resolve Reviewer 1.2's findings, and verify implementation offline.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

TASKS:
1. Create `voice_assistant/wiki.py` with:
   - `WikiRetriever` class:
     - `__init__(self, data_paths: list)`: Reads and parses the specified paths (e.g. `excel_output.txt` and `script.txt` from project root). Clean data (remove NaN, ignore lines with only separator chars like dashes/equals/vertical bars, strip whitespace). Build a simple TF-IDF or BM25 index on these text chunks. To maximize robustness and avoid external library dependencies, you should write a pure-Python TF-IDF ranker, but you can also use sklearn if available.
     - `retrieve(self, query: str, top_k: int = 2) -> list[str]`: Tokenizes the query, scores the indexed chunks, and returns the top `top_k` matching chunks as a list of strings. Validates that `query` is a non-empty string and `top_k` is a positive integer.
2. Update `voice_assistant/llm.py`:
   - Initialize model in `LLMEngine.__init__` using memory-safe loading parameters `low_cpu_mem_usage=True` and `device_map="auto"` in `AutoModelForCausalLM.from_pretrained`.
   - Update `LLMEngine.generate_response(self, prompt: str, context: list = None, retrieval_context: str = "") -> str`:
     - If `context` is `None`, default it to `[]` and do NOT throw a `TypeError` (resolving Reviewer 1.2 finding).
     - Incorporate `retrieval_context` (a string) into the generation. If `retrieval_context` is present, format/prepend it to the prompt or system messages so the LLM uses it.
3. Verify:
   - Run the script `python verify_stt_llm.py` to ensure it runs correctly and can transcribe and generate responses using local models.
   - Run python to inspect if WikiRetriever works correctly.
   - Ensure the code complies with all interface contracts.
   
DELIVERABLE:
Write a handoff report at `e:\test\mvc-simulation\.agents\worker_stt_llm_2\handoff.md` detailing:
- Observation (what was changed)
- Logic Chain (reasons for changes)
- Caveats (any limitations or assumptions)
- Conclusion
- Verification results (command executed and output)

## 2026-06-21T02:01:28Z
You are the Voice Assistant Developer. Your objective is to complete the implementation of the local offline bilingual voice assistant ("Nàng thơ") in Python under voice_assistant/, incorporating R5 (Wiki RAG) and R6 (Hardware Optimization).

Please perform the following steps:
1. Inspect the existing code in voice_assistant/config.py, tts.py, stt.py, llm.py, and wiki.py.
2. Update voice_assistant/config.py:
   - Ensure DEFAULT_VOLUME = 0.5.
   - Define config parameters: DYNAMIC_MODEL_LOADING, STT_DEVICE, LLM_DEVICE, TTS_DEVICE, CACHE_DIR, MODEL_CACHE_DIR, DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES.
3. Update voice_assistant/stt.py:
   - Implement STTEngine to run Whisper on CPU (device="cpu", compute_type="int8").
   - Support dynamic loading/unloading with load_model() and unload_model().
   - In transcribe(audio_path_or_data), if DYNAMIC_MODEL_LOADING is True and the model is not loaded, raise RuntimeError.
4. Update voice_assistant/llm.py:
   - Implement LLMEngine to run Qwen 2.5 instruct (e.g. unsloth--qwen2.5-7b-instruct-unsloth-bnb-4bit or similar cached models) on GPU (device="cuda") with low_cpu_mem_usage=True and device_map="auto".
   - Support dynamic loading/unloading with load_model() and unload_model(). In unload_model(), call torch.cuda.empty_cache() and gc.collect().
   - In generate_response(prompt, context, retrieval_context), if DYNAMIC_MODEL_LOADING is True and the model is not loaded, raise RuntimeError. Ensure context defaults to [] if None.
5. Implement voice_assistant/controller.py:
   - Implement AssistantController coordinating: input -> STT (if voice) -> RAG retrieve -> LLM generate -> TTS speak.
   - Use threading.RLock for thread safety, and ensure any incoming input (text/voice) immediately stops TTS speech playback (preemption) and logs/processes the new input.
   - Respect DYNAMIC_MODEL_LOADING, loading STT model before transcription and unloading it immediately after, and loading LLM model before generation and unloading it immediately after (using try...finally blocks to ensure unloading).
6. Implement voice_assistant/main.py:
   - CLI entry point parsing --mode (text/voice), --input, --volume, and --offline-check.
7. Support Live E2E tests:
   - Update tests/run_tests.py to check if MOCK_ENGINES == "0" (live mode) and not override it.
   - Update tests/mock_assistant.py so that when MOCK_ENGINES == "0" (live mode), the mock classes (TTSEngine, STTEngine, LLMEngine, AssistantController) delegate the actual operations to the real classes (using importlib/sys.modules trick to import the real implementation without infinite recursion), while keeping history tracking active.
8. Execute the E2E tests:
   - Run in Mock mode first: py tests/run_tests.py (ensure all 90 tests pass).
   - Run in Live mode: Set MOCK_ENGINES=0 and run py tests/run_tests.py (ensure all 90 tests pass).
9. Run all other empirical and adversarial tests (e.g. tests/run_adversarial_diagnostics.py, tests/test_empirical_challenges.py, test_tts_adversarial.py) to verify the system's correctness, robustness, and interruption control. Fix any bugs found.
10. Document all actions, command outputs, and changes in handoff.md in your directory (.agents/worker_stt_llm_2/handoff.md).
