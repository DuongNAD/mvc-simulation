# Handoff Report - Milestone 1: TTS & Volume Challenger 2

## 1. Observation

I ran empirical and stress testing of the real Text-to-Speech (TTS) engine and volume control implementation (`voice_assistant/tts.py` and `voice_assistant/config.py`) across all three supported backends: `win32com`, `pyttsx3`, and `powershell`. 

Three test scripts were created and executed:
1. `tests/test_tts_adversarial.py` - Standard adversarial tests.
2. `tests/test_pyttsx3_limit.py` - Limit verification for `pyttsx3` preemption counts.
3. `tests/run_adversarial_diagnostics.py` - Diagnostic runner that generates `tests/adversarial_report.md`.

Direct observations and execution logs reveal the following behaviors and errors:

### Observation A: pyttsx3 Backend Failure under Stress Preemption
When calling `speak()` in rapid succession with zero or negligible delays, the `pyttsx3` backend fails to play subsequent speech requests after a threshold of preemptions (usually between 10 and 15 calls). The engine fails silently, with `is_speaking()` returning `False` and no audio playing.
Verbatim command output from `py tests/test_pyttsx3_limit.py`:
```
2026-06-20 23:02:07,189 [INFO] Testing pyttsx3 limit with 15 preemptions...
2026-06-20 23:02:07,189 [INFO] TTSEngine: Forced to use pyttsx3 backend.
2026-06-20 23:02:07,646 [INFO] After 15 preemptions, is_speaking: True
2026-06-20 23:02:07,846 [INFO] Final speak call is_speaking: False
2026-06-20 23:02:07,846 [ERROR] FAILURE: pyttsx3 failed to speak after 15 preemptions.
2026-06-20 23:02:07,906 [ERROR] First failure occurred at count: 15
```

### Observation B: Asynchronous Error Swallowing and Recovery for Invalid Volume Type
When passing an invalid volume type (e.g. `volume="loud"`), the main thread does not raise an exception. Instead, the background worker thread raises a `TypeError` when evaluating the clamping logic, which is caught and logged, allowing the worker thread to recover and process subsequent requests.
Verbatim worker thread error log during `run_adversarial_diagnostics.py`:
```
2026-06-20 23:03:01,268 [ERROR] Error in win32com worker loop: '<' not supported between instances of 'str' and 'float'
2026-06-20 23:03:08,695 [ERROR] Error in pyttsx3 worker loop: '<' not supported between instances of 'str' and 'float'
2026-06-20 23:03:15,496 [ERROR] Error in powershell worker loop: '<' not supported between instances of 'str' and 'float'
```

### Observation C: Asynchronous Error Swallowing and Recovery for Invalid Text Type
When passing an invalid text type (e.g. an integer `12345`) to the `powershell` backend, the worker thread raises an `AttributeError` when attempting string manipulation (`text.replace`), which is caught and logged without crashing the background thread.
Verbatim worker thread error log during `run_adversarial_diagnostics.py`:
```
2026-06-20 23:03:16,098 [ERROR] Error in powershell worker loop: 'int' object has no attribute 'replace'
```

### Observation D: Divergence Between Mock Engine and Real Engine Behavior
In `tests/test_tier2_boundaries.py`, the test suite runs with mock engines and asserts that:
- `engine.speak("Hello", volume=1.1)` raises `ValueError`.
- `engine.speak("Hello", volume=-0.1)` raises `ValueError`.
- `engine.speak("Hello", volume="high")` raises `TypeError`.
- `engine.speak(None, volume=0.5)` raises `TypeError` (mock class behavior).

However, on the real engine:
- `engine.speak("Hello", volume=1.1)` does NOT raise `ValueError` (it clamps it to 1.0).
- `engine.speak("Hello", volume=-0.1)` does NOT raise `ValueError` (it clamps it to 0.0).
- `engine.speak("Hello", volume="high")` does NOT raise `TypeError` in the main thread (it raises `TypeError` in the worker thread, which is logged and swallowed).
- `engine.speak(None, volume=0.5)` does NOT raise `TypeError` (it is ignored and returns immediately).

### Observation E: pyttsx3 volume=0.0 Behavior
When `volume < 0.0` is passed, the value is clamped to `0.0`. On `pyttsx3`, speaking at volume `0.0` (mute) causes `is_speaking()` to return `False` shortly thereafter (within 0.2 seconds), indicating that the engine immediately finishes or treats mute speaking as inactive, whereas `win32com` and `powershell` report `is_speaking = True` during mute speech.

---

## 2. Logic Chain

1. **Preemption Stress**: Under the hood, `speak()` empties the queue, sets `stop_requested = True`, and queues the new text. 
2. The worker thread status loop checks `self.stop_requested or not self.queue.empty()` to break out, terminate/stop current playback, end the run loop (`engine.endLoop()`), and start a new loop (`engine.startLoop(False)`) for the next item.
3. For `pyttsx3`, repeatedly ending and restarting the run loop rapidly causes comtypes/SAPI5 messages to fail to register new utterances. After ~15 rapid preemptions, the driver is corrupted, causing all subsequent `speak()` calls to fail silently.
4. **Invalid Inputs**: The implementation of `speak()` only validates `if not text: return`. It does not perform volume or type checks in the main thread.
5. In the worker threads, `max(0.0, min(1.0, volume))` clamps numeric out-of-bounds volumes, leading to graceful execution instead of exceptions.
6. Non-numeric volumes (e.g. `"loud"`) or non-string texts (e.g. `12345`) raise `TypeError`/`AttributeError` only when evaluated in the background thread. Because the background thread wraps each loop iteration in `except Exception as e`, it catches, logs, and swallows the error, resetting the speaking state. The caller is unaware of the failure except through logs.
7. **Concurrency safety**: Both `is_speaking()` (locked via `state_lock`) and `stop()` (locked via `action_lock`) operate safely under multi-threaded load, with no deadlocks, exceptions, or hung threads observed.

---

## 3. Caveats

- Testing was performed on a Windows system. The `win32com` SAPI5 backend and the `powershell` backend are Windows-specific. `pyttsx3` also resolves to SAPI5 on Windows. Behavior on Linux or macOS backends (e.g. `espeak`, `nsss`) was not tested.
- System-level audio resource contentions were not fully evaluated, but standard local execution ran successfully.

---

## 4. Conclusion

1. **Rapid Preemption**: Works robustly and does not crash for `win32com` and `powershell`. However, `pyttsx3` has a bug where it fails silently after approximately 15 rapid preemptions.
2. **Invalid Inputs**: The real engine handles invalid inputs gracefully (returns early or clamps volume). However, there is a **large mismatch** between the real engine and the mock engine. The mock engine raises exceptions for out-of-bounds and invalid volume/text types, whereas the real engine clamps values or fails/recovers silently on the background thread.
3. **Concurrency**: `is_speaking()` and `stop()` function correctly and safely under concurrent access.

---

## 5. Verification Method

To verify these results:
1. Run `py tests/run_adversarial_diagnostics.py`.
2. Inspect the generated file `tests/adversarial_report.md`.
3. Check the command output to verify the tests and exception logs.
