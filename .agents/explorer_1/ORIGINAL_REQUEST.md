## 2026-06-21T06:20:27Z

Investigate the workspace `e:\test\mvc-simulation` and:
1. Identify all obsolete voice assistant python test files and helper scripts under `tests/` that should be deleted.
2. Examine the current `index.html` to map out the elements (IDs, classes, layout) and check if any manual stepping buttons or controls exist (or are commented out).
3. Check the git status or git diff (if any) to see if there are concurrent changes from the implementation track.
4. Recommend a precise plan for implementing the E2E tests (Tiers 1-4) in `tests/test_mvc_flow.py` and the custom test runner `tests/run_tests.py`, explaining how we should handle the parallel implementation (e.g. if the stepping buttons are not yet implemented in `index.html`, how to structure the tests so they verify the planned structure and run properly, or if we can run them against a mocked/patched version of the page, or if we should write them to expect the elements).
Provide a structured report with file lists and recommendations in your handoff.
