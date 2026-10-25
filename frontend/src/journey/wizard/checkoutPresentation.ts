import type { Profile } from '../api';

export const readable = (value: string) => value.replaceAll('_', ' ');
export function formatDate(value: string | null | undefined) {
  if (!value) return 'Not answered';
  const date = new Date(`${value}T00:00:00Z`);
  return Number.isNaN(date.getTime()) ? 'Not answered' : new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' }).format(date);
}
export const wholeMoney = (pence: number) => new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP', minimumFractionDigits: pence % 100 ? 2 : 0, maximumFractionDigits: 2 }).format(pence / 100);
export function household(profile: Profile) {
  const adults = profile.people.filter(person => person.relationship !== 'child').length;
  const children = profile.people.length - adults;
  return [adults ? `${adults} adult${adults === 1 ? '' : 's'}` : '', children ? `${children} child${children === 1 ? '' : 'ren'}` : ''].filter(Boolean).join(', ') || 'No people added';
}
export function profileHeadline(profile: Profile) {
  return `${household(profile)}${profile.location.region ? `, ${profile.location.region}` : ''}.${profile.cover.start_date ? ` Starts ${formatDate(profile.cover.start_date)}.` : ''}`;
}
export const hospitalName = (tier: number | null) => tier === 2 ? 'Broader (demo)' : tier === 1 ? 'Standard (demo)' : 'No preference';
export function planName(name: string) {
  const research = /^Research (\d+)\s*\//.exec(name);
  return research ? `Health plan ${research[1]}` : name;
}
export function mustHaves(profile: Profile) {
  return [
    profile.budget.strict && profile.budget.monthly_pence !== null ? `budget up to ${wholeMoney(profile.budget.monthly_pence)} a month` : '',
    profile.excess.strict && profile.excess.max_pence !== null ? `excess up to ${wholeMoney(profile.excess.max_pence)}` : '',
    profile.hospital_list.minimum_tier ? `${profile.hospital_list.minimum_tier === 2 ? 'broader' : 'standard'} hospital access (demo)` : '',
    profile.cover.underwriting_required ? `${readable(profile.cover.underwriting || 'specified')} underwriting` : '',
    profile.outpatient.required && profile.outpatient.minimum_annual_pence !== null ? `outpatient cover of at least ${wholeMoney(profile.outpatient.minimum_annual_pence)} a year` : '',
    ...(profile.benefits.required?.map(readable) || []),
  ].filter(Boolean);
}
