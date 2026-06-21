# Project Plan - Java MVC Educational Simulation (orchestrator_gen2)

## Overview
We are implementing the new requirement R6: Deep-Dive Class Explanations & I/O Mapping, which requires that at each step of the simulation, the UI includes a highly detailed explanation panel answering three questions for the currently active class/file:
1. Real-world purpose of the specific class (plain, beginner-friendly language).
2. Exact data (Input) it is receiving right now.
3. Action it takes on that data, and the exact data (Output) it prepares to send to the next layer.

## Milestones and Plan Steps
1. **Assessment & Analysis (Milestone 11)**
   - Determine layout changes for `index.html` to host the new explanation panel.
   - Formulate the detailed explanation text mappings for all 7 steps.
2. **UI Implementation (Milestone 12)**
   - Add a dedicated, highly visible explanation panel in the visual layout of `index.html`.
   - Dynamically update the panel content at each step to answer the three questions for the active class/file.
   - Ensure the styling integrates cleanly with Tailwind CSS and matches the existing theme.
3. **E2E & Adversarial Test Suite Update (Milestone 13)**
   - Extend `tests/test_mvc_flow.py` to programmatically assert the existence, visibility, and correct text content (purpose, input, output) of the explanation panel at each of the 7 steps.
   - Handle the new elements in the test run gracefully.
4. **E2E Verification & Challenger Hardening (Milestone 14)**
   - Execute the test suite and confirm all 11+ test cases pass cleanly.
   - Invoke Challenger to stress-test UI stepping and check for regressions.
5. **Forensic Audit (Milestone 15)**
   - Invoke `teamwork_preview_auditor` to audit the code changes for authenticity, robustness, and compliance.
6. **Handoff & Final Validation (Milestone 16)**
   - Publish updated `PROJECT.md`, `TEST_INFRA.md`, and `TEST_READY.md`.
   - Hand over the finalized solution.
