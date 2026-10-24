import type { Profile } from '../api';

export const stages = ['About you', 'Your cover', 'Fine-tune', 'Your plans'];
export const benefitGroups: Record<string, string[]> = {
  hospital: ['inpatient', 'diagnostics', 'outpatient', 'cancer', 'emergency'],
  wellbeing: ['mental_health', 'physio'], everyday: ['dental', 'maternity', 'chronic', 'pre_existing'],
};
export const steps = [
  { id: 'consent', title: 'Before we start.', stage: 0, tier: 'Optional', fields: [] },
  { id: 'people', title: 'Who needs cover?', stage: 0, tier: 'Mandatory', fields: ['people'] },
  { id: 'region', title: 'Where do you live?', stage: 0, tier: 'Mandatory', fields: ['location'] },
  { id: 'start-date', title: 'When should cover start?', stage: 0, tier: 'Mandatory', fields: ['cover'] },
  { id: 'budget', title: 'Your monthly budget.', stage: 1, tier: 'Mandatory', fields: ['budget'] },
  { id: 'excess', title: 'Your maximum excess.', stage: 1, tier: 'Mandatory', fields: ['excess'] },
  { id: 'hospitals', title: 'Hospital access.', stage: 1, tier: 'Mandatory', fields: ['hospital_list'] },
  { id: 'benefits/hospital', title: 'Hospital and treatment.', stage: 1, tier: 'Mandatory', fields: ['benefits'] },
  { id: 'benefits/wellbeing', title: 'Mind and body.', stage: 1, tier: 'Mandatory', fields: ['benefits'] },
  { id: 'benefits/everyday', title: 'Everyday and life events.', stage: 1, tier: 'Mandatory', fields: ['benefits'] },
  { id: 'ready', title: 'Your essentials are done.', stage: 1, tier: 'Checkpoint', fields: [] },
  { id: 'optional/existing-cover', title: 'Do you already have cover?', stage: 2, tier: 'Optional', fields: ['cover'] },
  { id: 'optional/underwriting', title: 'Your underwriting preference.', stage: 2, tier: 'Optional', fields: ['cover'] },
  { id: 'optional/outpatient', title: 'Outpatient appointments.', stage: 2, tier: 'Optional', fields: ['outpatient'] },
  { id: 'optional/postcode', title: 'A little more location detail.', stage: 2, tier: 'Optional', fields: ['location'] },
  { id: 'optional/conditions', title: 'An existing-condition scenario.', stage: 2, tier: 'Optional', fields: ['health'] },
  { id: 'review', title: 'Check your answers.', stage: 2, tier: 'Review', fields: [] },
];
export type Step = typeof steps[number];
export const pathFor = (id = '') => '/get-cover/quote'+(id ? '/'+id : '');
export function localDate(days = 0) { const day=new Date();day.setDate(day.getDate()+days);return `${day.getFullYear()}-${String(day.getMonth()+1).padStart(2,'0')}-${String(day.getDate()).padStart(2,'0')}`; }
export function problem(id: string, p: Profile): string {
  if (id === 'people' && (!p.people.length || p.people.some(person => {
    if (person.date_of_birth) {
      const born = new Date(person.date_of_birth+'T12:00:00'); const today = new Date();
      const age = today.getFullYear()-born.getFullYear()-Number(today.getMonth()<born.getMonth() || (today.getMonth()===born.getMonth() && today.getDate()<born.getDate()));
      return !Number.isFinite(age) || age < (person.relationship === 'child' ? 0 : 18) || age > (person.relationship === 'child' ? 17 : 85);
    }
    return person.age_years === null || !Number.isInteger(person.age_years) || person.age_years < (person.relationship === 'child' ? 0 : 18) || person.age_years > (person.relationship === 'child' ? 17 : 85);
  }))) return 'Add a person and a valid age: adults 18–85, children 0–17.';
  if (id === 'region' && !p.location.region) return 'Choose a region so we can check which plans are available there.';
  if (id === 'start-date') {
    const today = new Date(); today.setHours(0,0,0,0); const end = new Date(today); end.setDate(end.getDate()+365);
    const date = new Date((p.cover.start_date || '')+'T00:00:00');
    if (!Number.isFinite(+date) || date < today || date > end) return 'Choose a start date from today through 365 days ahead.';
  }
  if (id === 'budget' && (!p.budget.choice || (p.budget.choice === 'amount' && (p.budget.monthly_pence === null || p.budget.monthly_pence < 0 || p.budget.monthly_pence > 1000000)))) return 'Choose no target or enter a monthly budget up to £10,000.';
  if (id === 'excess' && (!p.excess.choice || (p.excess.choice === 'amount' && ![0,25000,50000].includes(p.excess.max_pence ?? -1)))) return 'Choose a maximum excess or no preference.';
  if (id === 'hospitals' && (!p.hospital_list.choice || (p.hospital_list.choice === 'minimum_tier' && ![1,2].includes(p.hospital_list.minimum_tier ?? 0)))) return 'Choose a hospital list or no preference.';
  if (id === 'benefits/everyday' && p.benefits.required === null) return 'Confirm that you have reviewed essential benefits, including choosing none.';
  if (id === 'optional/underwriting' && p.cover.underwriting_required && !['moratorium','full_medical'].includes(p.cover.underwriting || '')) return 'Choose a supported underwriting method before making it a must.';
  if (id === 'optional/outpatient' && (p.outpatient.required && p.outpatient.minimum_annual_pence === null || (p.outpatient.minimum_annual_pence ?? 0) > 10000000)) return 'Enter an annual minimum up to £100,000, or turn off the essential requirement.';
  if (id === 'optional/postcode' && p.location.postcode && !/^[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$/i.test(p.location.postcode)) return 'Enter a UK-format postcode, or skip this optional question.';
  return '';
}
export const essentials = ['people','region','start-date','budget','excess','hospitals','benefits/everyday'];
export const firstMissing = (p: Profile) => essentials.find(id => problem(id,p));
export function guardedStep(requested: string, p: Profile) {
  const target = steps.findIndex(s => s.id === requested);
  return steps.slice(0, Math.max(0,target)).find(s => s.tier === 'Mandatory' && problem(s.id,p))?.id;
}
