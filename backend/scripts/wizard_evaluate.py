"""Replay the checked-in synthetic personas; no provider calls or visitor data."""
import json
from datetime import date
from pathlib import Path

from app.journey.interviewer import current_question, parse_answer
from app.journey.schemas import JourneyProfile, completeness

root = Path(__file__).resolve().parents[2]
personas = json.loads((root/'docs/research/personas.json').read_text())
agreement = turns = calls = 0
for persona in personas:
    p = persona['profile']
    expected = JourneyProfile.model_validate({'people':[{'relationship':'lead_adult','age_years':p['age']}], 'location':{'region':p['region']}, 'cover':{'start_date':date.today()}, 'budget':{'choice':'amount','monthly_pence':p['budget_pence']}, 'excess':{'choice':'no_preference'}, 'hospital_list':{'choice':'no_preference'}, 'benefits':{'required':p['required']}})
    answers = {'people':str(p['age']), 'location':p['region'], 'cover':date.today().isoformat(), 'budget':str(p['budget_pence']/100), 'excess':'no preference', 'hospital_list':'no preference', 'benefits':', '.join(p['required']) or 'none'}
    actual = JourneyProfile()
    while not completeness(actual)['ready']:
        question = current_question(actual)
        actual, called = parse_answer(question, answers[question['fieldKey']], actual, False)
        turns += 1
        calls += int(called)
    agreement += sum(actual.model_dump()[key] == value for key,value in expected.model_dump().items())
total = len(personas)*len(JourneyProfile.model_fields)
report = {'personas':len(personas), 'compared_top_level_fields':total, 'matching_fields':agreement, 'field_agreement_percent':round(agreement/total*100,2), 'average_mandatory_turns':turns/len(personas), 'provider_calls':calls, 'deterministic_fallback_percent':100, 'method':'Synthetic extractor replay of seven common fields; nine canonical sections including defaults compared. Not live model accuracy or 60 browser journeys.'}
assert agreement == total and calls == 0
(root/'docs/ux/INTERVIEW_EVALUATION.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
