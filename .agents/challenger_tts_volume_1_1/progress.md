# Progress log

Last visited: 2026-06-20T16:05:00Z

- Inspected codebase and identified discrepancies between mock and real implementations.
- Wrote and executed empirical test scripts (`test_empirical_tts.py`, `test_empirical_concurrency.py`, `test_stop_race.py`).
- Confirmed that rapid preemption is stable and does not crash the SAPI backend.
- Confirmed concurrency stability (no deadlocks or exceptions) for `is_speaking()` and `stop()`.
- Discovered and verified boundary failures: real engine silent-clamps instead of raising ValueError, and raises background TypeErrors instead of synchronous TypeErrors.
- Discovered background task leak in queue handling when exceptions occur.
- Logged all findings and generated `handoff.md`.
