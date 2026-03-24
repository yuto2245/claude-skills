import json
import secrets
from datetime import datetime
from random import SystemRandom

from memory_manager import append_record

RNG = SystemRandom()

NAMES = ['Aoi Nakamura', 'Haru Sato', 'Rin Takahashi', 'Yuki Ito', 'Mio Watanabe', 'Ren Kobayashi', 'Sora Tanaka', 'Nao Suzuki']
GENDERS = ['female', 'male', 'nonbinary']
CAREER_STAGES = ['new graduate', 'career changer', 'second-year engineer', 'junior transfer']
LEARNING_STYLES = ['theory-first', 'practice-first', 'question-driven', 'observation-first', 'trial-and-error']
STRENGTHS = ['logical reasoning', 'persistence', 'written communication', 'debugging patience', 'problem framing', 'team communication', 'curiosity']
WEAKNESSES = ['slows down on ambiguity', 'hesitates to ship early drafts', 'gets stuck polishing details', 'forgets to communicate blockers early', 'needs help turning feedback into action order']
BACKGROUNDS = ['Started in IT operations and moved into backend engineering after automating repetitive tasks.', 'Changed careers from customer support after building internal tools and SQL dashboards.', 'Joined from university research with hands-on ML exposure but limited production experience.', 'Came from a startup internship and is comfortable moving fast but needs stronger engineering habits.']
MOTIVATIONS = ['growth', 'impact', 'team', 'stability']
TEACHING_PREFERENCES = ['ask-back checkpoints', 'concrete examples', 'small milestones', 'written summaries', 'worked examples first']

def sample_big_five():
	return {
		'openness': RNG.randint(1, 5),
		'conscientiousness': RNG.randint(1, 5),
		'extraversion': RNG.randint(1, 5),
		'agreeableness': RNG.randint(1, 5),
		'neuroticism': RNG.randint(1, 5),
	}

def generate_persona():
	now = datetime.now()
	persona = {
		'id': 'junior-{}-{}'.format(now.strftime('%Y%m%d-%H%M%S'), secrets.token_hex(3)),
		'name': RNG.choice(NAMES),
		'gender': RNG.choice(GENDERS),
		'age': RNG.randint(22, 30),
		'career_stage': RNG.choice(CAREER_STAGES),
		'big_five': sample_big_five(),
		'learning_style': RNG.choice(LEARNING_STYLES),
		'strengths': RNG.sample(STRENGTHS, 3),
		'weaknesses': RNG.sample(WEAKNESSES, 2),
		'background': RNG.choice(BACKGROUNDS),
		'motivation': RNG.choice(MOTIVATIONS),
		'teaching_preferences': RNG.sample(TEACHING_PREFERENCES, RNG.randint(2, 3)),
		'created_at': now.replace(microsecond=0).isoformat(),
	}
	append_record('personas', persona)
	print(json.dumps(persona, ensure_ascii=False, indent=2))
	return persona

if __name__ == '__main__':
	generate_persona()
