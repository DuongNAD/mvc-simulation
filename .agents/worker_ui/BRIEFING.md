# BRIEFING — 2026-06-21T13:30:00+07:00

## Mission
Modify `index.html` to implement step-by-step manual transition controls, embed Java snippets for each step, and design a copy interface/tab where the user can view/copy complete production-style Java code files.

## 🔒 My Identity
- Archetype: UI Worker
- Roles: implementer, qa, specialist
- Working directory: e:\test\mvc-simulation\.agents\worker_ui
- Original parent: c214c1d3-dc04-48da-8ddb-0f48264fab32
- Milestone: Interactive Flow & UI / Java Snippets & Reference

## 🔒 Key Constraints
- Keep Vietnamese (lang="vi") locale for all explanations and UI labels.
- Design must use Tailwind CSS for modern, clean, responsive look.
- Stepping backwards from Step 5 must correctly roll back the database additions (pop student from the database in-memory array `db`).
- Embed Java snippets for steps 1-7.
- Render Java snippets contextually in the active step.
- Design tabbed copy interface/tab where the user can view/copy complete production-style Java code files (Main, Controller, Service, Repository, Model, DTOs, View, Validation).

## Current Parent
- Conversation ID: c214c1d3-dc04-48da-8ddb-0f48264fab32
- Updated: 2026-06-21T13:30:00+07:00

## Task Summary
- **What to build**: Next/Prev transition controls, database rollback on step 5->4, step-by-step contextual Java snippets, and a tabbed copy interface with full production-style Java files.
- **Success criteria**: Buttons are functional, DB rollback works, step-by-step snippets render correctly, full source code copy tab is clean and responsive. All verified by Playwright script.
- **Interface contracts**: e:\test\mvc-simulation\.agents\sub_orch_impl_mvc\SCOPE.md / PROJECT.md
- **Code layout**: index.html

## Key Decisions Made
- Use a two-tab container on the right panel. Tab 1: "Luồng Mô Phỏng" (Visual Flow + current step code + payload monitor). Tab 2: "Mã Nguồn Toàn Bộ" (Full Production-Style Java files).
- Keep HTML UI clean and aligned with original style.
- Verification automated using Playwright in headless mode.

## Change Tracker
- **Files modified**: index.html (simulation logic, manual controls, contextual snippets panel, tabbed production-code copy tab)
- **Build status**: PASS (verified using E2E Playwright script)
- **Pending issues**: None

## Quality Status
- **Build/test result**: PASS
- **Lint status**: 0 violations
- **Tests added/modified**: E2E verification test script written in .agents/worker_ui/verify_ui.py

## Artifact Index
- e:\test\mvc-simulation\index.html — Frontend simulation page
