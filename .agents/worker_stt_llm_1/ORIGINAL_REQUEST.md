## 2026-06-20T16:20:02Z
You are a Worker agent for Milestone 2: STT & LLM in the bilingual voice assistant project.
Your working directory is e:\test\mvc-simulation\.agents\worker_stt_llm_1.

Your task:
1. Implement `voice_assistant/stt.py` containing an `STTEngine` class:
   - Interface contract:
     - `transcribe(self, audio_path: str) -> str`: Transcribes local audio file.
   - It must utilize `faster-whisper` (you can try to `pip install faster-whisper`).
   - Load the model weights (`base` or `small`) from the local HF cache `C:\Users\Admin\.cache\huggingface\hub` (e.g., `models--Systran--faster-whisper-base` or `models--Systran--faster-whisper-small`).
   - Run on GPU (`cuda`) if PyTorch CUDA is available, or fallback to CPU.
2. Implement `voice_assistant/llm.py` containing an `LLMEngine` class:
   - Interface contract:
     - `generate_response(self, prompt: str, context: list = None) -> str`: Generates assistant response using Qwen 2.5.
   - It must load the pre-downloaded Qwen 2.5 Instruct model (e.g., `models--Qwen--Qwen2.5-7B-Instruct` or similar version in cache) from local HF cache `C:\Users\Admin\.cache\huggingface\hub` using `transformers`.
   - Run on GPU (`cuda`) to ensure fast local response.
3. Verify both modules:
   - Create a test script `verify_stt_llm.py` to verify that `STTEngine` transcribes audio files offline, and `LLMEngine` generates responses from the local Qwen model.
   - Execute the verification, capture the output, and document it in your handoff report `handoff.md`.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
