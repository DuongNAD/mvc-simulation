# Analysis Report: Codebase & Architecture Discovery for Bilingual Voice Assistant

## Executive Summary
This report analyzes the existing files in the workspace `E:\test\mvc-simulation` and provides recommendations for the architecture and tech stack of the upcoming bilingual (Vietnamese/English) voice assistant project. 

Our investigation confirms that:
1. The existing Java codebase (`src/`) is an educational simulation of a Doctor Management System using the MVC design pattern, and is **not** the codebase for the voice assistant.
2. The other files in the workspace (`index.html`, `script.txt`, `excel_output.txt`, etc.) serve as instructional material explaining MVC and SOLID principles. The voice assistant is expected to act as an interactive tutor/companion (named "Nàng thơ") to explain these materials and support bilingual Q&A.
3. The voice assistant should be implemented as a **standalone Python application** rather than being integrated into the Java MVC codebase. This is supported by Python's superior ecosystem for offline speech processing (STT/TTS) and local LLMs, as well as the Python interface contracts defined in the global project specifications.

---

## 1. Review of Existing Code Files (`src/`)
We examined the Java files in the `src/` directory:
- **Structure**:
  - `src/main/Main.java`: Entry point for the CLI program. Reads input via `Scanner` and coordinates options.
  - `src/controller/DoctorController.java`: Intermediary layer between user request and repository, coordinating the View.
  - `src/model/Doctor.java`: Defines the core domain entity structure.
  - `src/repository/DoctorRepository.java`: Manages data persistence (CRUD actions) using a mock database (HashMap).
  - `src/dto/DoctorRequestDTO.java` & `dto/DoctorResponseDTO.java`: Clean data transfer objects separating user inputs and view models.
  - `src/view/DoctorView.java`: Formats outputs and writes to console.
  - `src/constants/Message.java` & `src/constants/Constants.java`: Shared literal values.
  - `src/utils/Validation.java`: Validates user inputs.

- **Relationship to Voice Assistant**:
  - **No Direct Functional Link**: The Java project is a complete, CLI-based Doctor Management System. It contains no speech-processing or AI code.
  - **Role**: This codebase acts as the **tutorial subject**. The voice assistant is expected to serve as a companion to guide students through this specific code, explaining its structure and layers.
  - **Action**: Do **not** modify or integrate into the Java source files. They must remain read-only as reference documentation/tests for the learning tool.

---

## 2. Review of Workspace Support Files
We reviewed the other files located in the root of the workspace:
- **`index.html`**: A frontend web page providing an interactive visual simulation of the MVC architecture (Main ↔ Controller ↔ Service ↔ Repository ↔ Model). It is written using Tailwind CSS and raw JS, simulating the addition of a Student entity.
- **`script.txt`**: A Vietnamese script spoken by a persona named "Nàng thơ" explaining each layer of the Doctor MVC project.
- **`GiaiThichMVC.mp3`**: A pre-recorded audio file of the Vietnamese speech script, representing a baseline TTS or voiceover.
- **`excel_output.txt`** (and its source `Guide OOP Lab.xlsx`): Detailed textual explanations of MVC layers and the 5 SOLID design principles, including Java code snippets violating/conforming to the principles.
- **`sample_sheet.csv`**: A CSV mapping the Java classes to their descriptions and duties.

These resources constitute the **knowledge base** for the voice assistant. The assistant will need to ingest, reference, or read these files to explain the Java codebase and SOLID principles to the student, and play or mimic the voice assistant persona "Nàng thơ".

---

## 3. Architecture & Tech Stack Recommendations (R1, R2, R3, R4)

We recommend a **Python-based standalone application** for the bilingual voice assistant.

### Python vs. Java Integration
- The global project specifications (`PROJECT.md`) describe the interfaces using Python type-hinting (`text: str, volume: float = 0.5`).
- Setting up offline, local AI (ASR, LLM, TTS) is highly optimized and widely supported in Python, whereas Java requires complex Native Interface bindings (JNI) or large native wrappers.
- The voice assistant will reside in a separate folder in the workspace (e.g. `voice_assistant/`) and interact with the workspace files using Python filesystem APIs.

### Proposed Tech Stack

| Module | Component | Recommended Stack | Rationale |
|---|---|---|---|
| **R1: TTS** | Text-to-Speech Engine | `piper` (using ONNX Runtime) OR `kokoro-onnx` | Local execution. Both support high-quality bilingual (Vietnamese/English) voices with a soft, natural voice profile. They run efficiently on CPU. (Fallback: `pyttsx3`/`pyttsx4` using Windows SAPI5, though voice options may vary). |
| **R2: STT** | Speech-to-Text (ASR) | `vosk-api` (Vosk) OR `faster-whisper` | Vosk is lightweight (~50MB models), fully offline, highly accurate in Vietnamese and English, and runs fast on CPU with Windows. Whisper-based options offer higher accuracy but consume more resources. |
| **R3: Volume** | Audio Playback & Control | `pygame` (mixer) OR `sounddevice` | Allows loading synthesized audio, adjusting starting playback volume to a default `< 100%` (e.g., `0.5` or 50%), and raising/lowering volume programmatically. |
| **R4: LLM** | Local Conversational AI | `ollama` (via `ollama` python client) OR `llama-cpp-python` | If Ollama is running locally, we can easily query a Vietnamese-adapted model (e.g., `VinaLlama` or `Qwen2.5-7B-Instruct`). If self-contained, `llama-cpp-python` can run a GGUF model directly inside the Python process. |
| **Control Loop** | Coordinating Loop | `threading` or `asyncio` | Manages the main user-assistant interaction loop. Multi-threading is required to monitor for user text/voice input during TTS audio playback, enabling immediate interruption. |
| **User Interface** | GUI/CLI | `customtkinter` (GUI) or `argparse`/`cmd` (CLI) | A simple CLI is sufficient for core control. A GUI using `customtkinter` (modern Tkinter wrapper) can easily display status, transcriptions, and host a volume slider. |

### Interruptibility Mechanism (R2 Detail)
To support real-time voice and text interruption:
1. **TTS Playback Thread**: When the assistant is speaking, audio chunks are streamed to the output device.
2. **Input Monitor Thread**: Concurrently, the ASR engine listens to the microphone (or monitors CLI standard input for text).
3. **Interruption Event**: If a user voice activity (VAD) is detected or the user types a character, an `InterruptEvent` is set.
4. **Playback Stop**: The playback thread checks this event flag before playing each audio chunk. If set, playback stops instantly (`stop()`), the current audio buffer is cleared, and the control loop transitions to transcribing and responding to the new query.
