## 2026-06-20T16:16:05Z

You are a Worker agent for Milestone 1 (TTS & Volume) - Iteration 3 in the voice assistant project.
Your working directory is e:\test\mvc-simulation\.agents\worker_tts_volume_3.

Your task is to implement the following robust improvements to `voice_assistant/tts.py`:
1. Input Validation: In `speak()`, raise a `TypeError` if `text` is not an instance of `str`.
2. Race Conditions: Eliminate the boolean `stop_requested` flag. Instead, implement a monotonically increasing integer `self.speech_id` initialized to 0 under locks. Every speak and stop call increments this ID. Dequeue the ID with the item. In the worker threads, check if `item_id != self.speech_id` to detect if the current item is preempted or stopped, and break/terminate playback immediately.
3. Thread Target Reference Cycle: Avoid bound method references in `threading.Thread` to prevent memory leaks. Change the thread target to a `@staticmethod` taking weak references or passing queue/locks/events directly:
   `self.worker_thread = threading.Thread(target=TTSEngine._worker_thread_entry, args=(weakref.ref(self), ...), daemon=True)`
4. PowerShell backend warning: In `_run_powershell`, redirect subprocess `stdout` and `stderr` to `subprocess.DEVNULL` instead of `subprocess.PIPE` to prevent pipe descriptor leaks and `ResourceWarning`.
5. Pyttsx3 Exception Handling: Wrap the pyttsx3 speaking and polling loop in a `try...finally` block to guarantee `engine.endLoop()` is called even if COM exceptions occur.

Run the tests (verify_tts.py, test_tts_adversarial.py) to verify the fixes and detail it in your handoff report `handoff.md`.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
