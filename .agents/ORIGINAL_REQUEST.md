# Original User Request

## Initial Request — 2026-06-20T15:41:34Z

An interactive voice assistant application featuring a soft, highly accurate bilingual (Vietnamese and English) voice using local offline models. It supports real-time Q&A so the user can interrupt to ask for clarifications via voice or text, and includes an adjustable volume control (starting at a lower default volume).

Working directory: ~/teamwork_projects/interactive_voice_assistant
Integrity mode: benchmark

## Requirements

### R1. Bilingual Soft Voice TTS
The application must feature an offline Text-to-Speech (TTS) system capable of reading both Vietnamese and English text with high pronunciation accuracy and a soft voice profile.

### R2. Interruptible Q&A (Voice & Text)
The application must allow the user to interrupt the assistant's speech at any time to ask clarification questions. Input can be provided via text or voice (utilizing a local ASR model like Nemotron 3 ASR or similar offline alternatives).

### R3. Volume Control
The application must include an adjustable volume control. The default starting volume must be explicitly configured to a level lower than the system's maximum (e.g., 50%).

### R4. Local Execution
The core STT, TTS, and conversational AI logic must run locally without relying on paid external APIs, utilizing open-source or local offline models.

## Acceptance Criteria

### TTS Verification
- [ ] An automated test script successfully generates audio files for both English and Vietnamese text inputs using the integrated local TTS model.

### Interruptibility Verification
- [ ] An automated or simulated test demonstrates that while audio is playing, a new text or simulated voice input immediately stops the current playback and successfully logs/processes the new input.

### Volume Configuration
- [ ] The codebase explicitly defines the default volume setting at `< 100%` (or `< 1.0`), verifiable by inspecting the configuration or UI startup properties.

### Offline Operation
- [ ] An agent-as-judge or automated script verifies that the application can initialize and process an end-to-end request (STT -> LLM -> TTS) without making external HTTP requests to paid APIs.

## Follow-up — 2026-06-20T16:27:05Z

USER COMMAND: PAUSE EXECUTION. The user is currently playing a game and needs the CPU/GPU resources. Please immediately suspend all heavy tasks, kill any running Python processes that use PyTorch/CUDA, and pause the orchestration until further notice. Do not run any further E2E tests for now.

## Follow-up — 2026-06-21T01:12:35Z

USER COMMAND: RESUME EXECUTION. The user has finished playing their game and wants to continue the project. Note: The server was restarted, so you are being revived. Please resume orchestration, restart your background cron jobs, and continue working on Milestone 3 (Interruption Control / AssistantController) and the rest of the project.

## Follow-up — 2026-06-21T01:13:03Z

USER ADDED NEW REQUIREMENT (R5): Please integrate a Wiki/Knowledge Base into the LLM pipeline (e.g., using RAG - Retrieval-Augmented Generation with Wikipedia or a local wiki) to ensure the AI relies on factual data and avoids hallucinating information. Update your Orchestrator's plans and milestones to include this new requirement.

## Follow-up — 2026-06-21T01:23:15Z

USER COMMAND: RESUME EXECUTION & NEW REQUIREMENT (R6). The server restarted, so you are being revived. The user complained that the current implementation consumes too much hardware resource (VRAM/RAM/CPU). Please add a new requirement (R6 - Hardware Optimization). You must aggressively optimize resource usage for the user's RTX 5060 Ti. Solutions to implement: use smaller model variants (e.g., whisper 'tiny' or 'base', smaller LLMs like Qwen-1.5B or 0.5B instead of 7B), implement dynamic model loading/unloading (do not keep STT, LLM, TTS, and RAG embeddings all in VRAM simultaneously), or offload some components to CPU. Please update the orchestrator plans, restart your cron jobs, and resume the implementation.

## Follow-up — 2026-06-21T04:14:34Z

An interactive web-based educational simulation that breaks down the Java MVC (Model-View-Controller) architecture. It visually demonstrates the data flow using a concrete mock scenario (e.g., Student Management System) and provides step-by-step reference Java code snippets so the user can learn to build a similar project.

Working directory: e:\test\mvc-simulation
Integrity mode: development

## Requirements

### R1. Interactive MVC Flow Visualization
The application must serve an interactive web page that visually simulates the HTTP request and response lifecycle in a Java MVC application (e.g., Spring MVC). It must clearly show how data moves between the View, Controller, Service, and Model layers.

### R2. Contextual Scenario & Explanations
The simulation must be grounded in a concrete mock scenario (such as a "Student Management System"). As the visualization progresses through each layer, it must explain the specific role and responsibility of the class currently handling the data.

### R3. Reference Java Code Generation
For each step in the MVC flow, the application must display corresponding, production-style Java code snippets (e.g., `@Controller`, `@Entity`, `.jsp` or `.html` templates) so the user can copy and practice building the project.

## Acceptance Criteria

### Flow Visualization Verification
- [ ] An automated browser test or agent-as-judge verifies that the web application loads without errors and contains interactive elements (e.g., "Next Step" buttons) that successfully transition the visual state from View -> Controller -> Model -> View.

### Code Snippet Presence
- [ ] A programmatic script or DOM parser verifies that the web page explicitly renders distinct sections containing Java code for at least one Model class, one Controller class, and one View template.

## Follow-up — 2026-06-21T11:35:05Z

An interactive web-based educational simulation that breaks down the Java MVC (Model-View-Controller) architecture. It visually demonstrates the data flow using a concrete mock scenario (e.g., Student Management System), explicitly tracks data passing between specific files, and provides step-by-step reference Java code snippets.

Working directory: e:\test\mvc-simulation
Integrity mode: development

## Requirements

### R1. Interactive MVC Flow Visualization
The application must serve an interactive web page that visually simulates the HTTP request and response lifecycle in a Java MVC application. It must clearly show how data moves between the View, Controller, Service, and Model layers.

### R2. Contextual Scenario & Explanations
The simulation must be grounded in a concrete mock scenario (such as a "Student Management System"). As the visualization progresses through each layer, it must explain the specific role and responsibility of the class currently handling the data.

### R3. Reference Java Code Generation
For each step in the MVC flow, the application must display corresponding, production-style Java code snippets.

### R4. Detailed File-Level Data Tracking (NEW)
The simulation must break down the data flow into highly granular steps. Instead of just showing abstract layers (e.g., "Controller -> Service"), it must explicitly trace the data payload moving between specific files (e.g., `StudentController.java` calling `StudentService.java`), showing exactly what data is being passed.

### R5. Progressive Diagram Breakdown (NEW)
The architectural diagram must not be presented as a single, complex, overwhelming graphic. It must be broken down into smaller, progressive visual steps that are easy for a beginner to digest one by one.

## Acceptance Criteria

### Flow Visualization Verification
- [ ] An automated browser test or agent-as-judge verifies that the web application loads without errors and contains interactive elements (e.g., "Next Step" buttons) that successfully transition the visual state.

### Code Snippet Presence
- [ ] A programmatic script or DOM parser verifies that the web page explicitly renders distinct sections containing Java code for at least one Model class, one Controller class, and one View template.

### Granularity Verification (NEW)
- [ ] An agent-as-judge verifies that the UI explicitly names the specific Java files currently interacting at each step (e.g., "StudentController.java"), rather than just the abstract architectural layer names.
- [ ] An agent-as-judge verifies that the visual diagram is presented in multiple sub-steps or progressively reveals itself, rather than displaying all connections statically at once.

## Follow-up — 2026-06-21T11:50:39Z

An interactive web-based educational simulation that breaks down the Java MVC (Model-View-Controller) architecture. It visually demonstrates the data flow using a concrete mock scenario (e.g., Student Management System), explicitly tracks data passing between specific files, provides step-by-step reference Java code snippets, and deeply explains the purpose and I/O of every class.

Working directory: e:\test\mvc-simulation
Integrity mode: development

## Requirements

### R1. Interactive MVC Flow Visualization
The application must serve an interactive web page that visually simulates the HTTP request and response lifecycle in a Java MVC application. It must clearly show how data moves between the View, Controller, Service, and Model layers.

### R2. Contextual Scenario & Explanations
The simulation must be grounded in a concrete mock scenario (such as a "Student Management System"). As the visualization progresses through each layer, it must explain the specific role and responsibility of the class currently handling the data.

### R3. Reference Java Code Generation
For each step in the MVC flow, the application must display corresponding, production-style Java code snippets.

### R4. Detailed File-Level Data Tracking
The simulation must break down the data flow into highly granular steps. Instead of just showing abstract layers, it must explicitly trace the data payload moving between specific files (e.g., `StudentController.java` calling `StudentService.java`).

### R5. Progressive Diagram Breakdown
The architectural diagram must be broken down into smaller, progressive visual steps that are easy for a beginner to digest one by one.

### R6. Deep-Dive Class Explanations & I/O Mapping (NEW)
At each step of the simulation, the UI must include a highly detailed explanation panel that answers three questions for the currently active class/file:
1. What is the real-world purpose of this specific class? (e.g., "Why do we need a Service class here instead of putting code in the Controller?")
2. What exact data (Input) is it receiving right now?
3. What is it doing with that data, and what exact data (Output) is it preparing to send to the next layer?

## Acceptance Criteria

### Flow Visualization & Granularity Verification
- [ ] An agent-as-judge verifies that the web application loads without errors, contains interactive "Next Step" buttons, and progressively reveals the visual state while naming specific Java files.

### Code Snippet Presence
- [ ] A programmatic script or DOM parser verifies that the web page explicitly renders distinct sections containing Java code for at least one Model class, one Controller class, and one View template.

### Deep-Dive Explanation Verification (NEW)
- [ ] An agent-as-judge verifies that at each step, there is a dedicated text section or panel that explicitly explains the class's purpose, its input data structure, and its output data structure in plain, beginner-friendly language.

