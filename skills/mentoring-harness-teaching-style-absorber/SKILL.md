---
name: mentoring-harness-teaching-style-absorber
description: Simulate and adapt mentoring for a junior engineer persona. Use when Codex needs to create a reusable junior-persona profile, tailor lesson plans to that persona, process code-review feedback into coaching guidance, or track mentoring progress across sessions.
---

# Mentoring Harness

Use this skill to run a persistent junior-mentoring simulation with deterministic helper scripts and lightweight memory.

## Workflow

1. Create or refresh a junior persona with `scripts/personality_generator.py` when the user asks to create a new junior, trainee, mentee, or "new hire" profile.
2. Read the latest persona from `data/memory.json` before producing any teaching plan, explanation style, or review coaching.
3. Use `scripts/lesson_planner.py` for teaching plans and concept breakdowns.
4. Use `scripts/review_processor.py` for review feedback rewrites and coaching suggestions.
5. Use `scripts/progress_tracker.py` after a lesson or review when the user wants progress recorded or summarized.

## Resource Map

- Read `references/soul.md` before changing persona-generation rules.
- Read `references/teaching_examples.md` when you need example adaptations by learning style.
- Use `scripts/memory_manager.py` for all memory reads and writes instead of editing `data/memory.json` manually.

## Operating Rules

- Keep persona generation non-sexual and workplace-relevant.
- Avoid fixed stereotypes; treat gender, age, and background as metadata, not as teaching determinants.
- Base adaptation on explicit traits such as learning style, strengths, weaknesses, recent progress, and review history.
- If the user names a specific persona ID, target that persona; otherwise use the most recent active persona.
