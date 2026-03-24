import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MEMORY_PATH = BASE_DIR / 'data' / 'memory.json'

def load_memory():
	if not MEMORY_PATH.exists():
		return {'principles': [], 'personas': [], 'progress': [], 'reviews': []}
	with MEMORY_PATH.open('r', encoding='utf-8') as handle:
		return json.load(handle)

def save_memory(memory):
	MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
	with MEMORY_PATH.open('w', encoding='utf-8') as handle:
		json.dump(memory, handle, ensure_ascii=False, indent=2)

def append_record(section, record):
	memory = load_memory()
	memory.setdefault(section, []).append(record)
	save_memory(memory)
	return record

def get_latest_persona(persona_id=None):
	personas = load_memory().get('personas', [])
	if persona_id:
		for persona in reversed(personas):
			if persona.get('id') == persona_id:
				return persona
		return None
	return personas[-1] if personas else None
