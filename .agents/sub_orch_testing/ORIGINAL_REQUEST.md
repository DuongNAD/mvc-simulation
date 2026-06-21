# Original User Request

## Initial Request — 2026-06-20T22:50:00Z

You are the E2E Testing Track Orchestrator for the bilingual voice assistant project.
Your mission is to design and implement a comprehensive, opaque-box, requirement-driven E2E test suite in Python.
Your working directory is e:\test\mvc-simulation\.agents\sub_orch_testing.
Read the global project scope at e:\test\mvc-simulation\.agents\orchestrator\PROJECT.md and the user request at e:\test\mvc-simulation\.agents\ORIGINAL_REQUEST.md.

You must:
1. Design TEST_INFRA.md at the project root (e:\test\mvc-simulation\TEST_INFRA.md) following the template in the orchestrator instructions.
2. Develop test cases using the 4-tier methodology (N = 5 features):
   - Tier 1: Feature Coverage (>= 5 per feature, happy-path, e.g. text/voice inputs, output audio check, volume config, local models).
   - Tier 2: Boundary & Corner cases (>= 5 per feature, e.g., empty input, extremely long text, special characters, volume limits, double interruptions, silent voice input).
   - Tier 3: Cross-feature combinations (pairwise interaction of major features).
   - Tier 4: Real-world application scenarios (at least 5 application scenarios like tutoring dialogs, volume adjustments, live voice interruption).
   - Total minimum test count: ~57 cases (5 * 5 + 5 * 5 + 5 + 5 = 60).
3. Provide a test runner (tests/run_tests.py) that returns exit code 0 on success. The test suite must be opaque-box (not importing implementation internal python modules directly; testing using CLI execution or public APIs/entrypoints where possible, or mock interfaces).
4. Once the test suite is fully created and you verify it, publish TEST_READY.md at the project root e:\test\mvc-simulation\TEST_READY.md.

Follow the Project Sub-orchestrator pattern:
- Assess whether your scope fits a single loop or decomposition.
- You can spawn teamwork_preview_worker to write the test script files.
- When finished, write your handoff report and notify the parent orchestrator (conversation ID: ebfe9089-500d-4cd7-9f3c-8c685a02bf12).

Remember the MANDATORY INTEGRITY WARNING: Do not hardcode test results. All implementations must be genuine.
