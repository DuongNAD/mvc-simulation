# Project: Interactive Voice Assistant

## Architecture
The application is a Python-based interactive voice assistant (code-named "Nàng thơ") designed to run entirely locally and offline on Windows. It consists of:
1. **TTS Engine (`voice_assistant/tts.py`)**: Local Text-to-Speech engine supporting soft bilingual (VI/EN) voice profiles using SAPI5 (Windows native TTS) as a default local engine, with extensible support for local ONNX/Piper models. SAPI5/edge-tts runs on CPU.
2. **STT Engine (`voice_assistant/stt.py`)**: Local Speech-to-Text engine using `faster-whisper` loading cached model weights (`small`/`base`/`tiny`) from the Hugging Face cache. STT is configured to run on CPU (or dynamically loaded/unloaded) to save VRAM.
3. **LLM Engine (`voice_assistant/llm.py`)**: Local Large Language Model client using Hugging Face `transformers` to run the pre-downloaded `Qwen2.5-7B-Instruct-AWQ` or smaller models (like cached 2B parameters models) on the GPU (`cuda`).
4. **Wiki/Knowledge Base RAG Engine (`voice_assistant/wiki.py`)**: A local offline information retriever (using TF-IDF or BM25 index on local files/guides/markdown) running on CPU that retrieves factual context for the LLM to prevent hallucinations.
5. **Hardware Optimization Manager (`voice_assistant/config.py`)**: Implements dynamic model loading/unloading (unloading STT model before LLM execution, unloading LLM model before long-duration TTS execution, and explicitly calling `torch.cuda.empty_cache()` and Python `gc.collect()`), CPU offloading for STT and TTS, and uses smaller cached models (e.g. whisper-base and Qwen 2.5 7B AWQ or Gemma 4 2B) to protect the RTX 5060 Ti 8GB VRAM limits.
6. **Control Coordinator (`voice_assistant/controller.py`)**: A multi-threaded controller that manages the input/output loop, volume scaling, and real-time interruption (immediately halting audio playback when new input is received).

## Code Layout
- `voice_assistant/`
  - `__init__.py`
  - `config.py` - Volume, models, dynamic loading/unloading configurations, and device settings.
  - `tts.py` - TTS Engine class with `speak(text, volume)` and `stop()`.
  - `stt.py` - STT Engine class with `transcribe(audio_path)` and memory cleanup hooks.
  - `llm.py` - LLM Engine class with `generate_response(prompt, retrieval_context)` and dynamic load/unload methods.
  - `wiki.py` - local offline retriever indexing local documents (MVC guides, SOLID rules).
  - `controller.py` - Main execution loop with threading, interruption logic, dynamic memory scheduling, and RAG coordination.
  - `main.py` - Entry point to start the CLI or UI assistant.
- `tests/`
  - `run_tests.py` - Automated test runner.
  - `test_tts.py` - Automated TTS output tests.
  - `test_interruption.py` - Simulated playback interruption tests.
  - `test_volume.py` - Verifies startup and runtime volume settings.
  - `test_rag.py` - Verifies local wiki indexing, retrieval, and LLM augmentation.
  - `test_optimization.py` - Verifies dynamic loading/unloading, CPU offloading, and GPU memory usage.
  - `test_offline.py` - Verify system runs end-to-end without paid external API calls.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | System Discovery | Analyze system environment, Python version, audio drivers, and recommend models. | None | DONE |
| 2 | Test Infra & Suite | E2E Testing Track: Design test suite, write runner & tests (Tiers 1-4), publish `TEST_READY.md`. (Resumed: Adding R5 RAG & R6 Hardware Optimization tests). | M1 | IN_PROGRESS |
| 3 | Offline TTS & Volume | Implementation Track: Implement TTS engine (SAPI5/local) with adjustable volume control (default 50%). | M1 | DONE |
| 4 | Offline STT, LLM, RAG & Opt | Implementation Track: Implement local STT, LLM, local wiki RAG engine (`wiki.py`), and R6 dynamic model load/unload. | M1 | IN_PROGRESS |
| 5 | Interruption Control | Implementation Track: Implement the multi-threaded controller loop enabling text/voice interruption of playback. | M3, M4 | PLANNED |
| 6 | Integration & Verification | Implementation Track: Run the full E2E test suite (Tiers 1-4), resolve failures, and achieve 100% pass rate. | M2, M5 | PLANNED |
| 7 | Adversarial Hardening | Phase 2: Challenger-driven white-box testing of untested code paths (Tier 5). | M6 | PLANNED |

## Interface Contracts
### TTS Interface (`voice_assistant.tts.TTSEngine`)
- `speak(text: str, volume: float = 0.5)` -> None: Speaks the text at the given volume (0.0 to 1.0) on a background thread.
- `stop()` -> None: Immediately halts any ongoing speech playback.
- `is_speaking()` -> bool: Returns whether audio is currently playing.

### ASR Interface (`voice_assistant.stt.STTEngine`)
- `transcribe(audio_path_or_data)` -> str: Transcribes local audio file or microphone input to text.
- `load_model()` -> None: Loads the Whisper model.
- `unload_model()` -> None: Unloads the Whisper model and frees memory.

### Wiki/RAG Interface (`voice_assistant.wiki.WikiRetriever`)
- `retrieve(query: str, top_k: int = 2)` -> list[str]: Retrieves relevant factual text blocks from the local knowledge base.

### LLM Interface (`voice_assistant.llm.LLMEngine`)
- `generate_response(prompt: str, context: list, retrieval_context: str = "")` -> str: Generates response using Qwen 2.5/Gemma, augmented by factual context.
- `load_model()` -> None: Loads the LLM model into GPU VRAM.
- `unload_model()` -> None: Unloads the LLM and calls `torch.cuda.empty_cache()` and `gc.collect()`.

### Controller Interface (`voice_assistant.controller.AssistantController`)
- `start()` -> None: Starts the main user-assistant interaction loop.
- `handle_input(input_type: str, content: str_or_audio)` -> None: Handles new incoming user message, stopping current playback.
