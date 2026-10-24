"""Plain-English templates over frozen, deterministic policy facts."""
from .policy import pounds


def band(value):
    if value is None:
        return 'Not established'
    return 'Excellent' if value >= 90 else 'Strong' if value >= 75 else 'Fair' if value >= 55 else 'Limited'


def explanation(item, profile_version):
    plan, quote = item['plan'], item['quote']
    components = item['standard']['components']
    ratings = {name:band(value) for name,value in components.items()}
    covered = [f"{care.replace('_',' ')}: up to {pounds(limit)} a year" for care,limit in plan['limits'].items() if limit]
    excluded = [care.replace('_',' ') for care,limit in plan['limits'].items() if not limit]
    scenarios = [f"In the fictional {name.replace('_',' ')} scenario, the plan pays {pounds(value['insurer_pence'])} and you pay {pounds(value['member_pence'])} in treatment costs, including excess and any uncovered costs. Annual premium plus your treatment cost: {pounds(value['annual_total_pence'])}." for name,value in item['scenarios'].items()]
    sections = [
        {'id':'fit','title':'Why this plan fits you','paragraphs':['This option meets your confirmed hard requirements. The ranking is a synthetic comparison, not personal advice.', '; '.join(f"{name.replace('_',' ').capitalize()}: {label.lower()}" for name,label in ratings.items())+'.'], 'sources':['confirmed_profile.hard_requirements','standard.components']},
        {'id':'covered','title':"What's covered",'paragraphs':covered or ['No positive benefit caps are established in this snapshot.'], 'sources':['plan.limits']},
        {'id':'excluded','title':"What's not covered",'paragraphs':['Not included / zero benefit: '+(', '.join(excluded) or 'none specified')+'.',f"Existing-condition status: {plan['pre_existing']}. Existing conditions are never assumed covered."], 'sources':['plan.limits','plan.pre_existing']},
        {'id':'pay','title':"What you'll pay",'paragraphs':[f"Monthly base {pounds(quote['base_pence'])} plus assumed tax {pounds(quote['tax_pence'])}: {pounds(quote['monthly_pence'])} total. Annual premium {pounds(quote['annual_pence'])}.",f"Excess {pounds(plan['excess_pence'])}, applied {plan['excess_application'].replace('_',' ')}. Copayment {plan['copay']*100:g}% of eligible treatment after excess.",*scenarios,'Fixed one-adult scenarios, not forecasts for your household or maximum-loss guarantees.'], 'sources':['quote','plan.excess_pence','plan.copay','scenarios']},
        {'id':'conditions','title':'Conditions and waiting periods','paragraphs':[f"Underwriting: {plan['underwriting'].replace('_',' ')}. {plan['referral']}.",'This snapshot does not establish waiting periods or individual medical acceptance. Ask a broker to check what is missing.'], 'sources':['plan.underwriting','plan.referral']},
        {'id':'hospitals','title':'Hospital access','paragraphs':[f"Fictional hospital-list tier {plan['network']}. This does not establish access to a real hospital or provider network."], 'sources':['plan.network']},
        {'id':'method','title':'How we estimate','paragraphs':['The server applies availability and hard requirements first, then reference product and confirmed-preference scores. The first three matches come from different policy families. Prices use integer pence, fictional family terms and a labelled12% tax assumption.','Unknown or excluded required cover fails. Hard requirements are never silently relaxed.'], 'sources':['engine_version','standard','contextual','fusion','quote.assumptions']},
    ]
    return {'plan_id':item['id'],'profile_version':profile_version,'sections':sections,'ratings':ratings,'numbers':{'standard':item['standard'],'contextual':item['contextual'],'fusion':item['fusion'],'alpha':item['alpha']},'provider_called':False}


def main_differences(items):
    if len(items) < 2:
        return 'Choose at least two plans to compare their differences.'
    cheapest = min(items,key=lambda i:(i['quote']['monthly_pence'],i['id']))
    lowest = min(items,key=lambda i:(i['plan']['excess_pence'],i['id']))
    lines = [f"{cheapest['plan']['name']} has the lowest monthly premium here at {pounds(cheapest['quote']['monthly_pence'])}.", f"{lowest['plan']['name']} has the lowest excess here at {pounds(lowest['plan']['excess_pence'])}."]
    for item in items:
        if item['id'] != cheapest['id']:
            delta=item['quote']['monthly_pence']-cheapest['quote']['monthly_pence']
            lines.append(f"{item['plan']['name']} costs {pounds(delta)} more per month than {cheapest['plan']['name']}; its outpatient cap is {pounds(item['plan']['limits']['outpatient'])}, and its fictional hospital tier is {item['plan']['network']}.")
    return ' '.join(lines)
