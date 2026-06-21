# Scope: Local Offline Bilingual Voice Assistant ("Nàng thơ") Implementation

## Architecture
- `voice_assistant/config.py`: stores configuration parameters (e.g. startup volume, cache paths, hardware settings).
- `voice_assistant/tts.py`: provides text-to-speech utilizing SAPI5 on Windows as a fallback, or Piper/Kokoro ONNX models.
- `voice_assistant/stt.py`: provides speech-to-text utilizing faster-whisper on CUDA.
- `voice_assistant/llm.py`: Qwen 2.5 local offline LLM client via transformers.
- `voice_assistant/wiki.py`: local retrieval engine indexing local text files for factual context to LLM.
- `voice_assistant/controller.py`: orchestrates the STT-LLM-TTS loop, handles background voice/text playback, and implements real-time interruption (halting TTS speech output immediately upon user input).
- `voice_assistant/main.py`: main entry point CLI interface.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | TTS & Volume | Implement config.py and tts.py. Ensure SAPI5 works offline and supports volume controls (default 50%). | None | DONE |
| 2 | STT, LLM & Wiki RAG | Implement stt.py (faster-whisper), llm.py (local Qwen 2.5), and local RAG retrieval in wiki.py to retrieve factual context for Qwen prompting. | None | IN_PROGRESS |
| 3 | Interruption Control | Implement controller.py and main.py CLI with threading. Interruption halts playback immediately. | M1, M2 | PLANNED |
| 4 | Integration & Verification | Wait for TEST_READY.md, run the E2E test suite, fix bugs to achieve 100% pass rate. | M3 | PLANNED |
| 5 | Adversarial Hardening | Phase 2 coverage hardening. Generate adversarial inputs, run white-box analysis, fix gaps. | M4 | PLANNED |

## Interface Contracts
### TTS Interface (`voice_assistant.tts.TTSEngine`)
- `__init__(self)`
- `speak(self, text: str, volume: float = 0.5)` -> None: Speaks the text on a background thread.
- `stop(self)` -> None: Halts any ongoing playback.
- `is_speaking(self)` -> bool: Returns true if speaking.

### STT Interface (`voice_assistant.stt.STTEngine`)
- `__init__(self)`
- `transcribe(self, audio_path: str)` -> str: Transcribes local audio file.

### LLM Interface (`voice_assistant.llm.LLMEngine`)
- `__init__(self)`
- `generate_response(self, prompt: str, context: list)` -> str: Generates response using local model.

### Wiki Interface (`voice_assistant.wiki.WikiRetriever`)
- `__init__(self, data_paths: list)`
- `retrieve(self, query: str, top_k: int = 3) -> str`: Returns combined factual context text from indexed files.

### Controller Interface (`voice_assistant.controller.AssistantController`)
- `__init__(self)`
- `start(self)` -> None: Starts the main user-assistant interaction loop.
- `handle_input(self, input_type: str, content: str)` -> None: Handles new incoming message, immediately interrupting playback if speaking.
