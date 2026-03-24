import json, sys
from memory_manager import get_latest_persona

GUIDE = {'theory-first': 'Start with principles, then examples.', 'practice-first': 'Start with a small task, then explain.', 'question-driven': 'Pause often for questions and restatements.', 'observation-first': 'Show a full example before guided practice.', 'trial-and-error': 'Use safe experiments and quick feedback.'}

def build_plan(topic, persona_id=''):
	persona = get_latest_persona(persona_id or None)
	if not persona:
		raise SystemExit('No persona found. Generate a persona first.')
	return {
		'persona_id': persona['id'],
		'topic': topic,
		'approach': GUIDE[persona['learning_style']],
		'lesson_steps': ['Explain why it matters.', 'Teach one core model.', 'Run guided practice.', 'Close with recap and next step.'],
		'coaching_checkpoints': [
			'Strengths: {}'.format(', '.join(persona['strengths'])),
			'Weaknesses: {}'.format(', '.join(persona['weaknesses'])),
			'Preferences: {}'.format(', '.join(persona['teaching_preferences'])),
		],
	}

if __name__ == '__main__':
	if len(sys.argv) == 1:
		raise SystemExit('Usage: lesson_planner.py topic [persona_id]')
	persona_id = sys.argv[2] if len(sys.argv) == 3 else ''
	print(json.dumps(build_plan(sys.argv[1], persona_id), ensure_ascii=False, indent=2))
