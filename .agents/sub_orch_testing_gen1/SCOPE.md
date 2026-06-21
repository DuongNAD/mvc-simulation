# Scope: Milestone 2 Resumed - R5 RAG & R6 Hardware Optimization Verification

## Architecture
- `voice_assistant.wiki.WikiRetriever`: Retrieves local text chunks.
- `voice_assistant.llm.LLMEngine`: Accepts `retrieval_context`, supports `load_model()` and `unload_model()`.
- `voice_assistant.stt.STTEngine`: Supports `load_model()`, `unload_model()`, and CPU offloading.
- `voice_assistant.tts.TTSEngine`: Supports CPU/SAPI5 execution.
- `voice_assistant.config`: Dynamic loading/unloading configurations and device settings.
- `voice_assistant.controller.AssistantController`: Orchestrates dynamic load scheduling, RAG, and I/O.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | R5 RAG Test Infra | Revise TEST_INFRA.md, mock_assistant.py, and test_rag.py (Tiers 1-4). | None | DONE |
| 2 | R6 Opt Feature Inventory | Revise TEST_INFRA.md at project root to add R6 Optimization details. | M1 | PLANNED |
| 3 | Mock Optimization | Update tests/mock_assistant.py to support load/unload, tracking, and config devices. | M2 | PLANNED |
| 4 | Implement Opt Tests | Implement tests/test_optimization.py (Tiers 1-4). | M3 | PLANNED |
| 5 | Run & Verify all tests | Ensure run_tests.py runs test_rag.py and test_optimization.py, exit code is 0. | M4 | PLANNED |
| 6 | Publish Attestation | Revise TEST_READY.md at project root with results (75 + new optimization tests). | M5 | PLANNED |

## Interface Contracts
### WikiRetriever
- `retrieve(query: str, top_k: int = 2)` -> list[str]: Retrieves up to top_k matching chunks.

### STTEngine
- `load_model()` -> None
- `unload_model()` -> None

### LLMEngine
- `load_model()` -> None
- `unload_model()` -> None

### AssistantController
- Dynamic model loading schedule (ensures STT and LLM models are not loaded in VRAM at the same time if DYNAMIC_MODEL_LOADING is enabled).
