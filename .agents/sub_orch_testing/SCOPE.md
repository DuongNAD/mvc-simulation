# Scope: Test Infra & Suite (Milestone 2)

## Architecture
- **E2E Test Runner**: `tests/run_tests.py` which discovers and executes all test cases.
- **Opaque-box Execution**: The tests interact with the application via public CLI commands (`py -m voice_assistant.main`) or public engine API contracts without importing internal helper modules directly.
- **Mock / Simulator Drivers**: For audio recording, playback, and network checks, standard mock configurations or test environment mocks may be used to verify control flow and interruption timings reliably without hardware dependencies.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Test Infra Plan & Setup | Design `TEST_INFRA.md` and project structure. | None | PLANNED |
| 2 | Tier 1: Feature Coverage | Implement happy-path tests for TTS, STT, LLM, Interruption, Volume (25 cases). | M1 | PLANNED |
| 3 | Tier 2: Boundary & Edge | Implement boundary & corner case tests for the 5 features (25 cases). | M2 | PLANNED |
| 4 | Tier 3: Cross-Feature | Implement pairwise feature combination tests (5 cases). | M3 | PLANNED |
| 5 | Tier 4: Real-World Scenarios| Implement application workloads (5 scenarios). | M4 | PLANNED |
| 6 | Test Runner & Verification | Implement `tests/run_tests.py`, execute tests, publish `TEST_READY.md`. | M5 | PLANNED |

## Interface Contracts
The tests will interact with the voice assistant via:
1. **CLI Commands**:
   - `py -m voice_assistant.main --mode text --input "Hello"` -> outputs response text and plays audio.
   - `--volume <float>`: startup volume configuration.
   - `--offline-check`: run startup verification.
2. **Public Engine Classes** (if programmatically accessed):
   - `voice_assistant.tts.TTSEngine`: `speak(text, volume)`, `stop()`, `is_speaking()`
   - `voice_assistant.stt.STTEngine`: `transcribe(audio_path_or_data)`
   - `voice_assistant.llm.LLMEngine`: `generate_response(prompt, context)`
   - `voice_assistant.controller.AssistantController`: `start()`, `handle_input(input_type, content)`
