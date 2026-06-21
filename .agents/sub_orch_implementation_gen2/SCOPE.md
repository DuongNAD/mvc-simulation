# Scope: Local Offline Bilingual Voice Assistant ("Nàng thơ") Implementation

## Architecture
- `voice_assistant/config.py`: stores configuration parameters (e.g. startup volume 50%, models, hardware settings, dynamic loading flag).
- `voice_assistant/tts.py`: provides text-to-speech utilizing SAPI5 on Windows as a fallback, or Piper/Kokoro ONNX models. SAPI5/edge-tts runs on CPU.
- `voice_assistant/stt.py`: speech-to-text using Whisper (faster-whisper) configured for CPU execution.
- `voice_assistant/llm.py`: Qwen 2.5 local offline LLM client via transformers/AWQ running on GPU (CUDA), supporting dynamic load/unload and clearing CUDA cache.
- `voice_assistant/wiki.py`: local offline retriever indexing local documents (excel_output.txt, script.txt) using a pure Python TF-IDF/BM25 implementation to prevent hallucinations.
- `voice_assistant/controller.py`: coordinates the STT-LLM-TTS loop, handles background voice/text playback, and implements real-time interruption (halting TTS speech output immediately upon user input using RLock and thread preemption).
- `voice_assistant/main.py`: main entry point.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | TTS & Volume | Implement config.py and tts.py. Ensure SAPI5 works offline and supports volume controls (default 50%). | None | DONE |
| 2 | STT, LLM, RAG & Optimization | Implement stt.py (Whisper on CPU), llm.py (Qwen 2.5 on GPU with load/unload & CUDA cache clearing), wiki.py (pure Python TF-IDF indexer), config.py (VRAM tracking, volume 50%). | M1 | DONE |
| 3 | Interruption Control | Implement coordinator loop in controller.py and main.py CLI with threading. Interruption halts playback immediately. | M1, M2 | DONE |
| 4 | Integration & Verification | Disable mock mode, run the 90 E2E tests in live mode, fix bugs to achieve 100% pass rate. | M3 | DONE |
| 5 | Adversarial Hardening | Phase 2 coverage hardening. Generate adversarial inputs, run white-box analysis, fix gaps. | M4 | DONE |

## Interface Contracts
### TTS Interface (`voice_assistant.tts.TTSEngine`)
- `__init__(self)`
- `speak(self, text: str, volume: float = 0.5)` -> None: Speaks the text on a background thread.
- `stop(self)` -> None: Halts any ongoing playback.
- `is_speaking(self)` -> bool: Returns true if speaking.

### STT Interface (`voice_assistant.stt.STTEngine`)
- `__init__(self)`
- `transcribe(self, audio_path: str)` -> str: Transcribes local audio file.
- `load_model(self)` -> None: Loads Whisper model onto CPU.
- `unload_model(self)` -> None: Unloads Whisper model from memory.

### LLM Interface (`voice_assistant.llm.LLMEngine`)
- `__init__(self)`
- `generate_response(self, prompt: str, context: list, retrieval_context: str = "")` -> str: Generates response using local model.
- `load_model(self)` -> None: Loads Qwen model onto GPU (CUDA).
- `unload_model(self)` -> None: Unloads LLM and calls `torch.cuda.empty_cache()` and `gc.collect()`.

### Wiki Interface (`voice_assistant.wiki.WikiRetriever`)
- `__init__(self)`
- `retrieve(self, query: str, top_k: int = 2) -> list[str]`: Returns combined factual context text from indexed files.

### Controller Interface (`voice_assistant.controller.AssistantController`)
- `__init__(self)`
- `start(self)` -> None: Starts the main user-assistant interaction loop.
- `handle_input(self, input_type: str, content: str)` -> None: Handles new incoming message, immediately interrupting playback if speaking.
