import json, sys
from datetime import datetime
from memory_manager import append_record, get_latest_persona

def record_progress(topic, outcome, next_step, persona_id=''):
	persona = get_latest_persona(persona_id or None)
	if not persona:
		raise SystemExit('No persona found. Generate a persona first.')
	record = {
		'date': datetime.now().replace(microsecond=0).isoformat(),
		'persona_id': persona['id'],
		'topic': topic,
		'activity': 'mentoring-session',
		'outcome': outcome,
		'next_step': next_step,
	}
	append_record('progress', record)
	return record

if __name__ == '__main__':
	if len(sys.argv) != 4 and len(sys.argv) != 5:
		raise SystemExit('Usage: progress_tracker.py topic outcome next_step [persona_id]')
	persona_id = sys.argv[4] if len(sys.argv) == 5 else ''
	print(json.dumps(record_progress(sys.argv[1], sys.argv[2], sys.argv[3], persona_id), ensure_ascii=False, indent=2))
