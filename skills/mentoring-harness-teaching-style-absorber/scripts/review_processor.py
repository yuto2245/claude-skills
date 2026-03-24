import json, sys
from memory_manager import append_record, get_latest_persona

def process_review(review_text, persona_id=''):
	persona = get_latest_persona(persona_id or None)
	if not persona:
		raise SystemExit('No persona found. Generate a persona first.')
	result = {
		'persona_id': persona['id'],
		'source_review': review_text,
		'coach_summary': 'Turn the review into an ordered action list and confirm the target quality bar.',
		'actions': [
			'Rewrite feedback as next steps.',
			'Separate correctness from polish.',
			'Support weaknesses: {}'.format(', '.join(persona['weaknesses'])),
			'Use teaching style: {}'.format(persona['learning_style']),
		],
	}
	append_record('reviews', result)
	return result

if __name__ == '__main__':
	if len(sys.argv) == 1:
		raise SystemExit('Usage: review_processor.py review_text [persona_id]')
	persona_id = sys.argv[2] if len(sys.argv) == 3 else ''
	print(json.dumps(process_review(sys.argv[1], persona_id), ensure_ascii=False, indent=2))
