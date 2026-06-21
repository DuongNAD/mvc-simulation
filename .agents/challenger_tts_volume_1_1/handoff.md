# Handoff Report: TTS & Volume Empirical Stress Verification (Milestone 1)

This report presents the findings, empirical test results, and logic analysis for the local Text-to-Speech (TTS) and Volume implementation in `voice_assistant/tts.py` and `voice_assistant/config.py`.

---

## 1. Observation

### 1.1 Rapid Succession & Preemption (Stress Test)
*   **Command Executed**: `py tests/test_empirical_tts.py`
*   **Code Block Tested**: Rapid invocation of `TTSEngine.speak()` 50 times sequentially with varying volumes (0.1 to 0.9) and minimal delay (0.005s sleep).
*   **Result**: The SAPI `win32com` backend queued and preempted speech without crashing. The test output showed:
    ```
    === Test Stress Preemption ===
    Sending 50 speak calls in rapid succession...
    Sent 50 calls in 0.2699 seconds.
    Checking if engine is speaking...
    Engine speaking state after stress: True
    Stopping speech...
    Engine speaking state after stop: False
    Stress preemption test finished.
    ```

### 1.2 Invalid Inputs & Validation Discrepancy
*   **File Examined**: `voice_assistant/tts.py` lines 71-93 (`speak()` method):
    ```python
    def speak(self, text: str, volume: float = 0.5) -> None:
        """
        Speaks the text at the given volume (0.0 to 1.0) on a background thread.
        This call is non-blocking. It preempts/stops any ongoing speech immediately.
        """
        if not text:
            return

        with self.action_lock:
            # 1. Clear any pending speech requests in the queue
            while not self.queue.empty():
                try:
                    self.queue.get_nowait()
                    self.queue.task_done()
                except queue.Empty:
                    break

            # 2. Signal stop to the current speech loop
            self.stop_requested = True

            # 3. Queue the new speech request
            self.queue.put((text, volume))
    ```
*   **File Examined**: `tests/test_tier2_boundaries.py` lines 41-49:
    ```python
    def test_tts_speak_invalid_volume_high(self):
        engine = TTSEngine()
        with self.assertRaises(ValueError):
            engine.speak("Hello", volume=1.1)

    def test_tts_speak_invalid_volume_low(self):
        engine = TTSEngine()
        with self.assertRaises(ValueError):
            engine.speak("Hello", volume=-0.1)
    ```
*   **Command Executed**: `py tests/test_empirical_tts.py`
*   **Verbatim Outputs**:
    - **Volume `1.5`**: `Success: Call speak() with volume 1.5 returned.` (No `ValueError` raised).
    - **Volume `-0.5`**: `Success: Call speak() with volume -0.5 returned.` (No `ValueError` raised).
    - **Volume `"high"`**: `Success: Call speak() with volume='high' returned.` (No `TypeError` raised on caller thread).
      Background logs:
      `2026-06-20 23:02:17,426 [ERROR] voice_assistant.tts: Error in win32com worker loop: '<' not supported between instances of 'str' and 'float'`
    - **Volume `None`**: `Success: Call speak() with volume=None returned.` (No `TypeError` raised on caller thread).
      Background logs:
      `2026-06-20 23:02:17,862 [ERROR] voice_assistant.tts: Error in win32com worker loop: '<' not supported between instances of 'NoneType' and 'float'`

### 1.3 Queue Task Leak on Worker Exception
*   **File Examined**: `voice_assistant/tts.py` lines 185-192 (inside the SAPI worker loop `_run_win32com`):
    ```python
                except queue.Empty:
                    if self.stop_requested:
                        self.stop_requested = False
                    continue
                except Exception as e:
                    with self.state_lock:
                        self._is_speaking = False
                    logger.error(f"Error in win32com worker loop: {e}")
    ```
*   **Result**: When `TypeError` is raised inside the try block (e.g. at line 154 due to invalid volume types), it jumps to the `except Exception as e` handler. The line `self.queue.task_done()` is bypassed, causing the item retrieved by `self.queue.get()` to remain marked as unfinished indefinitely.

### 1.4 Concurrency Tests
*   **Command Executed**: `py tests/test_empirical_concurrency.py`
*   **Result**: 9 concurrent threads (4 reading `is_speaking()`, 3 calling `stop()`, and 2 calling `speak()`) ran for 3.0 seconds. Zero lockups, deadlocks, or exceptions were observed:
    ```
    Starting detailed concurrency verification...
    Launching 9 concurrent threads...
    All threads finished. Number of errors: 0
    No errors detected during concurrency test!
    ```

---

## 2. Logic Chain

1.  **Contract Mismatch**: 
    *   `tests/test_tier2_boundaries.py` expects that calling `speak()` with out-of-bounds volume raises `ValueError` synchronously, and invalid types raises `TypeError` synchronously.
    *   `voice_assistant/tts.py` contains no parameter validation logic on the `speak()` function entry point.
    *   Thus, the real implementation does not meet the interface boundary requirements asserted in the project's own test suite.

2.  **Silent Failures & Memory Leak**:
    *   Because parameter validation is missing on the main thread, invalid types (`None`, `str`) are successfully added to `self.queue`.
    *   When the worker thread attempts to clamp the volume (`int(max(0.0, min(1.0, volume)) * 100)`), it raises a `TypeError` on the background thread.
    *   The background thread catches the exception and logs it, but fails to call `self.queue.task_done()`.
    *   Therefore, any invalid input type causes a silent failure (no audio plays) and leaks a queue task entry.

3.  **Stability of Preemption & Concurrency**:
    *   `speak()` and `stop()` utilize `self.action_lock` to protect queue manipulation.
    *   `is_speaking()` and the worker loop utilize `self.state_lock` to protect the boolean `self._is_speaking`.
    *   No nested locks are used; thus, multi-threaded access is deadlock-free.
    *   Preemption works safely because the main thread clears the queue and sets `self.stop_requested = True`, which is subsequently handled by the polling loop on SAPI.

---

## 3. Caveats

*   **Active Backend**: All empirical tests were verified against the `win32com` SAPI5 backend, as it is the default backend initialized on this Windows environment.
*   **Other Backends**: The `pyttsx3` and `powershell` backends were not active during the empirical test run. However, code inspections confirm they suffer from the same lack of input validation and queue task leaks as SAPI5, because the `speak()` method itself is shared across all backends.

---

## 4. Conclusion

1.  **Stress Testing**: Preemption is robust and stable. Calling `speak()` repeatedly in rapid succession works correctly and does not crash SAPI5 or leak resources.
2.  **Concurrency**: Accessing `is_speaking()` and `stop()` concurrently under multi-threaded load is thread-safe and deadlock-free.
3.  **Invalid Input Handling (CRITICAL FAILURE)**: Invalid inputs are **not** handled gracefully.
    *   *Out-of-bounds volumes* are silently clamped instead of raising `ValueError`.
    *   *Invalid volume types* trigger background thread crashes, causing silent audio failure and task leaks in the `queue.Queue` structure, instead of throwing `TypeError` synchronously.
4.  **Action Needed**: Synchronous input checks must be added to `speak()` in `voice_assistant/tts.py` to match the project contracts and ensure errors are raised immediately on the caller thread.

---

## 5. Verification Method

To verify these results independently:
1.  **Run Empirical Stress & Invalid Inputs Test**:
    ```powershell
    py tests/test_empirical_tts.py
    ```
    *Observe that no exceptions are raised synchronously by `speak()` for volumes `1.5`, `-0.5`, `"high"`, or `None`.*
2.  **Run Concurrency Stress Test**:
    ```powershell
    py tests/test_empirical_concurrency.py
    ```
    *Observe that 9 threads concurrently running `speak()`, `stop()`, and `is_speaking()` execute without deadlocks or errors.*
3.  **Run Stop/Speak Race Test**:
    ```powershell
    py tests/test_stop_race.py
    ```
