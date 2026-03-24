# Junior Persona Generation Rules

## Purpose

Generate a realistic junior-engineer persona that can be reused across lessons, reviews, and progress tracking.

## Hard Constraints

- Do not generate sexualized, romantic, or appearance-based traits.
- Do not make teaching recommendations from gender, nationality, or age alone.
- Keep backgrounds plausible for early-career engineers or career changers.
- Keep outputs diverse by sampling multiple independent trait categories per run.

## Persona Schema

Store personas as JSON objects with these fields:

```json
{
 "id": "junior-20260309-120102-ab12cd",
 "name": "Aoi Nakamura",
 "gender": "nonbinary",
 "age": 26,
 "career_stage": "career changer",
 "big_five": {
 "openness": 4,
 "conscientiousness": 3,
 "extraversion": 2,
 "agreeableness": 5,
 "neuroticism": 3
 },
 "learning_style": "question-driven",
 "strengths": ["logical reasoning", "persistence", "written communication"],
 "weaknesses": ["slows down on ambiguity", "hesitates to ship early drafts"],
 "background": "Moved from operations into backend engineering after building internal automations.",
 "motivation": "growth",
 "teaching_preferences": ["ask-back checkpoints", "concrete examples", "small milestones"],
 "created_at": "2026-03-09T12:01:02"
}
```

## Trait Pools

- Big Five: 1 to 5 each.
- Learning style: `theory-first`, `practice-first`, `question-driven`, `observation-first`, `trial-and-error`.
- Motivation: `growth`, `impact`, `team`, `stability`.
- Teaching preferences: choose 2 or 3 signals that affect pacing and explanation style.

## Adaptation Guidance

- `question-driven`: prompt for questions, pause often, leave room for alternatives.
- `theory-first`: start with mental models, then examples.
- `practice-first`: start with a task, then explain underlying concepts.
- `observation-first`: show a worked example before guided practice.
- `trial-and-error`: provide safe experiments and fast feedback loops.
