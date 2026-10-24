"""Optional provider orders reviewed sentences; it cannot author customer facts."""
import json

from groq import Groq
from pydantic import Field

from ..config import settings
from .schemas import Strict


class SentenceOrder(Strict):
    order: list[int] = Field(min_length=1,max_length=20)


def narrate(reply,consent=False):
    if not consent or not settings().research_llm_enabled or not settings().groq_api_key:
        return {'reply':reply,'provider_called':False}
    sentences=reply.split('. ')
    try:
        response=Groq(api_key=settings().groq_api_key,timeout=8).chat.completions.create(model=settings().research_intent_model,temperature=0,response_format={'type':'json_object'},messages=[{'role':'system','content':'Arrange these reviewed sentences for clarity. Return JSON {order:[indices]} using every index exactly once. Do not write prose, omit a sentence, compute money, or create facts.'},{'role':'user','content':json.dumps(list(enumerate(sentences)))}])
        parsed=SentenceOrder.model_validate_json(response.choices[0].message.content or '{}')
        if sorted(parsed.order)!=list(range(len(sentences))):
            raise ValueError('Incomplete or invented sentence index')
        return {'reply':'. '.join(sentences[index] for index in parsed.order),'provider_called':True}
    except Exception:
        return {'reply':reply,'provider_called':False,'notice':'Provider unavailable or invalid. Showing the reviewed local explanation.'}
