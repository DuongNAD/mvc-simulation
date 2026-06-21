# BRIEFING — 2026-06-21T09:00:20+07:00

## Mission
Implement the local offline bilingual voice assistant ("Nàng thơ") in Python under voice_assistant/, incorporating R5 (Wiki RAG) and R6 (Hardware Optimization: smaller models, dynamic loading/unloading, CPU offloading), and verify with the 90 E2E tests in live mode.

## 🔒 My Identity
- Archetype: sub_orch_implementation_gen2
- Roles: orchestrator, user_liaison, human_reporter, successor
- Working directory: e:\test\mvc-simulation\.agents\sub_orch_implementation_gen2
- Original parent: main agent
- Original parent conversation ID: ebfe9089-500d-4cd7-9f3c-8c685a02bf12

## 🔒 My Workflow
- Pattern: Project
- Scope document: e:\test\mvc-simulation\.agents\sub_orch_implementation_gen2\SCOPE.md
1. **Decompose**: We divide our implementation into milestones (Milestone 1 completed, Milestone 2, Milestone 3, Milestone 4, Milestone 5).
2. **Dispatch & Execute**:
   - Direct (iteration loop): Spawn worker, reviewer, challenger, auditor to implement and verify each milestone.
3. **On failure** (in this order):
   - Retry: nudge stuck agent or re-send task
   - Replace: spawn fresh agent with partial progress
   - Skip: proceed without (only if non-critical)
   - Redistribute: split stuck agent's remaining work
   - Redesign: re-partition decomposition
   - Escalate: report to parent (last resort)
4. **Succession**: at 16 spawns, write handoff.md, spawn successor
- Work items:
  - Milestone 1: TTS & Volume [DONE]
  - Milestone 2: STT, LLM, RAG & Optimization [IN_PROGRESS]
  - Milestone 3: Interruption Control [PLANNED]
  - Milestone 4: Integration & Verification [PLANNED]
  - Milestone 5: Adversarial Hardening [PLANNED]
- Current phase: 2
- Current focus: Milestone 2: STT, LLM, RAG & Optimization

## 🔒 Key Constraints
- Local offline execution.
- Whisper model on CPU.
- Qwen 2.5 instruct model with CUDA (Transformers/AWQ), dynamic load/unload, clearing CUDA cache.
- Pure Python TF-IDF/BM25 indexing of MVC files (excel_output.txt and script.txt).
- Volume at 50% default.
- Never reuse a subagent after it has delivered its handoff.
- Forensic Auditor verdict must be CLEAN for milestones to pass.

## Current Parent
- Conversation ID: ebfe9089-500d-4cd7-9f3c-8c685a02bf12
- Updated: not yet

## Key Decisions Made
- Resuming from Milestone 2. We will spawn a worker to implement RAG, STT, LLM, config optimizations, and fix previous reviewer findings.

## Team Roster
| Agent | Type | Work Item | Status | Conv ID |
|-------|------|-----------|--------|---------|
| worker_stt_llm_2 | teamwork_preview_worker | Milestone 2-5 implementation & testing | completed | e5d77f3e-1530-45cd-bfa0-fd7ee6b1a9aa |
| auditor_implementation | teamwork_preview_auditor | Integrity audit of voice assistant | completed | 183eaa0f-1b40-4b88-a753-381f660b0008 |

## Succession Status
- Succession required: no
- Spawn count: 2 / 16
- Pending subagents: none
- Predecessor: sub_orch_implementation (gen1)
- Successor: not yet spawned

- Heartbeat cron: none
- Safety timer: none

## Artifact Index
- e:\test\mvc-simulation\.agents\sub_orch_implementation_gen2\progress.md — heartbeat progress file
- e:\test\mvc-simulation\.agents\sub_orch_implementation_gen2\SCOPE.md — scope description
