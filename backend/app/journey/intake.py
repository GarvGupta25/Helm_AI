import re
from decimal import ROUND_HALF_UP, Decimal

from ..research.generator import CARE
from .schemas import HELP, JourneyProfile


def propose(field: str, text: str, profile: JourneyProfile):
    """Controlled interviewer: captured fields, never provider-authored advice."""
    if field not in HELP:
        raise ValueError("Choose a supported intake question")
    if re.search(r'ignore (?:all|previous)|system prompt|jailbreak|<script', text, re.I):
        raise ValueError('Enter only your answer to the selected question, or use the manual form')
    text = text.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩٫", "0123456789."))
    for arabic, english in {"إنجلترا": "England", "انجلترا": "England", "لندن": "London", "اسكتلندا": "Scotland", "ويلز": "Wales", "أيرلندا الشمالية": "Northern Ireland", "لا تفضيل": "no preference", "لا هدف": "no target", "لا يوجد": "none", "صارم": "strict", "أوسع": "broader", "قياسية": "standard", "السرطان": "cancer", "الصحة النفسية": "mental health", "العيادات الخارجية": "outpatient"}.items():
        text = text.replace(arabic, english)
    lower = text.casefold()
    draft = profile.model_dump(mode="json")
    numbers = re.findall(r"\d+(?:\.\d{1,2})?", text)
    flexible = any(word in lower for word in ("no preference", "no target", "none", "flexible"))
    strict = any(word in lower for word in ("strict", "must", "hard"))
    if field == "people":
        ages = [int(n) for n in numbers if n.isdigit()]
        if not ages:
            raise ValueError("Enter ages, for example 35, 32, 8. Do not include names or medical details.")
        draft[field] = [{"relationship": "lead_adult" if i == 0 else "child" if age < 18 else "partner", "age_years": age} for i, age in enumerate(ages)]
    elif field == "location":
        region = next((r for r in ("Northern Ireland", "London", "Scotland", "Wales", "England") if r.casefold() in lower), None)
        if not region:
            raise ValueError("Choose England, London, Scotland, Wales, or Northern Ireland")
        draft[field]["region"] = region
    elif field == "cover":
        found = re.search(r"\d{4}-\d{2}-\d{2}", text)
        if not found:
            raise ValueError("Enter a start date as YYYY-MM-DD")
        draft[field]["start_date"] = found.group()
    elif field in {"budget", "excess"}:
        if flexible:
            draft[field] = {"choice": "no_target" if field == "budget" else "no_preference", "strict": False}
        else:
            if not numbers:
                raise ValueError("Enter an amount in pounds, or no preference")
            pence = int((Decimal(numbers[0])*100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            draft[field] = {"choice": "amount", "monthly_pence" if field == "budget" else "max_pence": pence, "strict": strict}
    elif field == "hospital_list":
        if flexible:
            draft[field] = {"choice": "no_preference"}
        else:
            tier = 2 if "broader" in lower or "2" in numbers else 1 if "standard" in lower or "1" in numbers else None
            if not tier:
                raise ValueError("Choose standard (1), broader (2), or no preference")
            draft[field] = {"choice": "minimum_tier", "minimum_tier": tier}
    elif field == "benefits":
        benefits = [care for care in CARE if care.replace("_", " ") in lower or care in lower]
        if not benefits and not flexible:
            raise ValueError("Name a supported benefit, or say none")
        required = list(profile.benefits.required or [])
        preferred = list(profile.benefits.preferred)
        if flexible:
            required, preferred = [], []
        elif any(word in lower for word in ("remove", "no longer", "don't need")):
            required = [b for b in required if b not in benefits]
            preferred = [b for b in preferred if b not in benefits]
        elif "prefer" in lower:
            preferred = list(dict.fromkeys(preferred+[b for b in benefits if b not in required]))
        else:
            required = list(dict.fromkeys(required+benefits))
            preferred = [b for b in preferred if b not in required]
        draft[field] = {"required": required, "preferred": preferred}
    return JourneyProfile.model_validate(draft)
