## 2026-06-20T16:04:07Z
You are a Worker agent for Milestone 1 (TTS & Volume) - Iteration 2 in the voice assistant project.
Your working directory is e:\test\mvc-simulation\.agents\worker_tts_volume_2.

Your task is to fix the issues discovered in the first implementation of `voice_assistant/tts.py` and `voice_assistant/config.py`:
1. Input Validation: Add synchronous validation checks in `speak()` (on the client thread):
   - volume must be a number (float or int), raise TypeError if not.
   - volume must be between 0.0 and 1.0 (inclusive), raise ValueError if not.
   - text cannot be None, raise TypeError if it is.
2. Immediate Stop / is_speaking() Race Condition: Ensure that when `stop()` is called, `is_speaking()` returns `False` immediately and synchronously. Set `self._is_speaking = False` under state_lock in `stop()` on the caller thread.
3. Queue Task Leak: Ensure that exceptions in the background worker thread loops (like SAPI or PowerShell calls) are caught so that `self.queue.task_done()` is always called.
4. Thread/Memory Leak: Add a `__del__` method to `TTSEngine` that calls `self.shutdown()`.
5. Verification: Run `py verify_tts.py` and run the adversarial tests to verify the fixes. Detail the commands and results in your handoff report `handoff.md`.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
