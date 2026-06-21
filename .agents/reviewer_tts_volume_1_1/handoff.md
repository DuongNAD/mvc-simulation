# Handoff Report — Reviewer 1 (Milestone 1: TTS & Volume)

## 1. Observation

1. **Test Runner Execution**: Running `py tests/run_tests.py` results in a success execution of 60 E2E tests:
   ```
   Total Tests Run: 60
   Passed:           60
   Failed:           0
   Errors:           0
   RESULT: PASS
   ```
   However, this execution has `MOCK_ENGINES = "1"` hardcoded in `tests/run_tests.py` (Line 7), causing all tests to use mock implementations from `tests/mock_assistant.py` rather than `voice_assistant/tts.py`.

2. **Volume Boundary Assertions**: `tests/test_tier2_boundaries.py` asserts that `ValueError` is raised synchronously when calling `speak()` with invalid volumes:
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

3. **Mock Engine Assertions**: In `tests/mock_assistant.py`, lines 35-41, the mock engine enforces synchronous type/range validation:
   ```python
   def speak(self, text: str, volume: float = 0.5):
       if not isinstance(volume, (int, float)):
           raise TypeError("Volume must be a number")
       if volume < 0.0 or volume > 1.0:
           raise ValueError("Volume must be between 0.0 and 1.0")
       if text is None:
           raise TypeError("Text cannot be None")
   ```

4. **Real Engine Implementation**: In `voice_assistant/tts.py`, lines 71-93, the real `speak()` method performs no input validation and clamps volume inside worker loops using:
   ```python
   # win32com backend
   voice.Volume = int(max(0.0, min(1.0, volume)) * 100)
   # pyttsx3 backend
   engine.setProperty("volume", max(0.0, min(1.0, volume)))
   # powershell backend
   vol_int = int(max(0.0, min(1.0, volume)) * 100)
   ```

5. **COM Apartment Safety**: In `voice_assistant/tts.py`, lines 135-195 (`_run_win32com`), the COM apartment is initialized and uninitialized on the background thread:
   ```python
   def _run_win32com(self):
       import pythoncom
       import win32com.client
       pythoncom.CoInitialize()
       voice = None
       try:
           voice = win32com.client.Dispatch("SAPI.SpVoice")
           # ...
       finally:
           voice = None  # Ensure COM object is released before CoUninitialize
           pythoncom.CoUninitialize()
   ```

6. **PowerShell Fallback Subprocess**: In `voice_assistant/tts.py`, lines 283-288, the PowerShell backend calls `subprocess.Popen` with standard pipes but never reads or closes them:
   ```python
   self.proc = subprocess.Popen(
       cmd,
       stdout=subprocess.PIPE,
       stderr=subprocess.PIPE,
       creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
   )
   ```

7. **PowerShell Text Escaping**: In `voice_assistant/tts.py`, line 271, single quotes are escaped using:
   ```python
   escaped_text = text.replace("'", "''")
   ```

---

## 2. Logic Chain

1. **Contract Discrepancy**: 
   * **Observation 2** establishes that boundary tests verify `ValueError` is raised when the volume is out-of-bounds (e.g. `1.1` or `-0.1`).
   * **Observation 3** shows that this expectation is fulfilled by the mock engine.
   * **Observation 4** shows that the real `TTSEngine` does not check or raise exceptions for out-of-bounds volumes, instead silently clamping them to `[0.0, 1.0]`.
   * **Conclusion**: If the E2E tests are executed against the actual `TTSEngine` implementation, the tests will fail. The real engine does not conform to the boundary contract defined in the test suite.

2. **Lack of Type Checks**:
   * **Observation 3** shows that the mock engine raises `TypeError` synchronously when invalid types are passed (e.g., `text=None` or `volume="abc"`).
   * **Observation 4** shows that the real `TTSEngine` does not validate parameter types synchronously. A non-numeric volume (e.g., `volume="abc"`) is queued and then crashes the background worker thread internally with a `TypeError` (caught and logged to console, but never raised to the caller). Passing `text=None` causes the real engine to return early (`if not text: return`) without raising `TypeError`.

3. **Subprocess Pipe Saturation Risk**:
   * **Observation 6** shows that `stdout=subprocess.PIPE` and `stderr=subprocess.PIPE` are initialized, but the outputs are never consumed.
   * **Reasoning**: If PowerShell outputs error traces or diagnostic logs that exceed the operating system's buffer limit, the process will block on writes and freeze the voice playback thread.
   * **Conclusion**: This poses a potential hang risk when operating under error states.

4. **COM Apartment Safety & Fallback Integrity**:
   * **Observation 5** demonstrates that `pythoncom.CoInitialize()` and `pythoncom.CoUninitialize()` are properly scoped to the background thread. Setting `voice = None` in the `finally` block before `CoUninitialize()` is the correct release pattern to prevent memory leaks and access violations.
   * Runtime tests executed on the Windows host platform confirm that all three backends (`win32com`, `pyttsx3`, `powershell`) initialize, process volumes, speak, and stop correctly when forced.

---

## 3. Caveats

* The STT and LLM components are out of scope for this review as they are not yet implemented on disk in this milestone (they exist only as mocks).
* The tests are currently restricted to Windows environments. The Linux/macOS fallback behaviors of SAPI5/pyttsx3 were not investigated.

---

## 4. Conclusion

The codebase demonstrates high-quality design for background thread orchestration, COM apartment safety, and robust PowerShell text sanitization and process interruption control.

However, there is a **conformance gap** between the expected boundary behavior (validated by `tests/test_tier2_boundaries.py`) and the actual implementation in `voice_assistant/tts.py`. Specifically, the real engine does not raise `ValueError` or `TypeError` synchronously for invalid inputs.

**Verdict**: **REQUEST_CHANGES**

---

## 5. Verification Method

To verify these findings independently, you can run the following inline Python scripts.

1. **Verify Backend Engines Execution**:
   Create and run a scratch script to test all three backends (`win32com`, `pyttsx3`, `powershell`) under real execution conditions:
   ```python
   import sys, time
   sys.path.insert(0, ".")
   from voice_assistant.tts import TTSEngine
   for backend in ["win32com", "pyttsx3", "powershell"]:
       print(f"Testing {backend}...")
       engine = TTSEngine(force_backend=backend)
       engine.speak(f"Testing {backend} backend.", volume=0.5)
       time.sleep(0.5)
       print(f"Is Speaking: {engine.is_speaking()}")
       engine.stop()
       time.sleep(0.1)
       print(f"After Stop Is Speaking: {engine.is_speaking()}")
       engine.shutdown()
   ```

2. **Verify PowerShell Escaping (Newlines, Quotes)**:
   Test how the PowerShell fallback command parses quote marks and newlines:
   ```python
   import sys, time
   sys.path.insert(0, ".")
   from voice_assistant.tts import TTSEngine
   engine = TTSEngine(force_backend="powershell")
   engine.speak("Line 1.\nLine 2.\nHe said 'Hello'.", volume=0.5)
   time.sleep(1.0)
   engine.shutdown()
   ```

3. **Verify Boundary Defect**:
   Run the following script to see that the real engine silently accepts an out-of-bounds volume without raising a `ValueError`:
   ```python
   import sys
   sys.path.insert(0, ".")
   from voice_assistant.tts import TTSEngine
   engine = TTSEngine()
   try:
       engine.speak("Should raise error", volume=1.5)
       print("FAIL: No ValueError raised for volume 1.5!")
   except ValueError:
       print("PASS: ValueError raised.")
   engine.shutdown()
   ```

---

## Quality Review Report

**Verdict**: REQUEST_CHANGES

### Findings

#### [Major] Finding 1: Volume Out-of-Bounds Error Handling Discrepancy
* **What**: The real `TTSEngine` silently clamps out-of-bounds volumes rather than raising a `ValueError`.
* **Where**: `voice_assistant/tts.py` lines 154, 213, 270.
* **Why**: The boundary tests in `tests/test_tier2_boundaries.py` (lines 41-50) assert that `ValueError` is raised synchronously. The tests only pass in mocked mode.
* **Suggestion**: Add synchronous validation in `TTSEngine.speak()`:
  ```python
  if volume < 0.0 or volume > 1.0:
      raise ValueError("Volume must be between 0.0 and 1.0")
  ```

#### [Major] Finding 2: Lack of Synchronous Type Checks for Input Arguments
* **What**: The real `TTSEngine` does not validate that `volume` is a number and that `text` is a string (or not None).
* **Where**: `voice_assistant/tts.py` lines 71-93.
* **Why**: If invalid types are passed, the background worker thread crashes internally or silently skips executing, which diverges from the mock's synchronous `TypeError` raising expected by the test suite.
* **Suggestion**: Add synchronous type checks in `TTSEngine.speak()`:
  ```python
  if not isinstance(volume, (int, float)):
      raise TypeError("Volume must be a number")
  if text is None:
      raise TypeError("Text cannot be None")
  ```

#### [Minor] Finding 3: Subprocess Pipe Saturation Risk in PowerShell Fallback
* **What**: The PowerShell backend uses `stdout=subprocess.PIPE` and `stderr=subprocess.PIPE` without reading or closing them.
* **Where**: `voice_assistant/tts.py` lines 283-288.
* **Why**: If PowerShell outputs logs or errors that fill the OS buffer, the process will block on writes and freeze the worker thread.
* **Suggestion**: Use `stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL` instead.

### Verified Claims

* `TTSEngine` Fallback Capability → verified via custom script forcing `"win32com"`, `"pyttsx3"`, and `"powershell"` backends sequentially → **PASS**
* COM Apartment safety on background thread → verified via code inspection and runtime verification → **PASS**

### Coverage Gaps

* **Actual (non-mocked) engine tests** — risk level: **medium** — recommendation: configure tests or write a separate test suite run that executes against the real engines if the host platform supports them.

### Unverified Items

* **STT and LLM implementations** — out of scope (these are not yet implemented on disk in this milestone, only mocked).

---

## Adversarial Challenge Report

**Overall risk assessment**: MEDIUM

### Challenges

#### [Medium] Challenge 1: Thread-Safety of `self._is_speaking` under High Concurrency
* **Assumption challenged**: The state flag `_is_speaking` is read and written thread-safely via `state_lock`.
* **Attack scenario**: If multiple calls to `speak()` and `stop()` occur concurrently from different threads, the state flag might briefly lag or read out of sync because `state_lock` is released quickly.
* **Blast radius**: Low. The state lock protects access correctly, but the non-blocking nature of `stop()` means that calling `stop()` and immediately querying `is_speaking()` (without a small yield/sleep) will return `True` (as observed in our initial run) because the background worker loop is polling.
* **Mitigation**: Document that `stop()` is asynchronous/non-blocking, or add a short wait option if synchronous halt confirmation is needed.

#### [Low] Challenge 2: Long Text Command Line Limit in PowerShell Fallback
* **Assumption challenged**: The PowerShell command line can handle any input text length.
* **Attack scenario**: If an extremely long text (exceeding ~8000 characters) is spoken via the PowerShell fallback, `subprocess.Popen` will crash due to Windows command-line string length limit.
* **Blast radius**: Low/Medium. The assistant will fail to speak and logs an error, but it won't crash the main application.
* **Mitigation**: Chunk the text into smaller sentences (e.g. < 1000 characters) before sending to PowerShell.

### Stress Test Results

* **Real backends execution** → Checked `win32com`, `pyttsx3`, and `powershell` → **PASS**
* **Special character and newline handling in PowerShell command string** → Checked text containing `'\n'`, `'\''`, and `'"'` → **PASS**

### Unchallenged Areas

* **Linux / macOS audio fallback dependencies** — reason not challenged: insufficient host environment context (Windows machine).
