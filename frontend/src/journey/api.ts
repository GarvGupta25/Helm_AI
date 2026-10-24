export type Person = { relationship: 'lead_adult' | 'partner' | 'child'; age_years: number | null; date_of_birth?: string | null; smoker_status?: string | null };
export type Profile = {
  people: Person[]; location: { region: string | null; postcode?: string | null };
  cover: { start_date: string | null; existing_cover?: string | null; underwriting?: string | null; underwriting_required: boolean };
  budget: { choice: string | null; monthly_pence: number | null; strict: boolean };
  excess: { choice: string | null; max_pence: number | null; strict: boolean };
  hospital_list: { choice: string | null; minimum_tier: number | null };
  outpatient: { minimum_annual_pence: number | null; required: boolean };
  benefits: { required: string[] | null; preferred: string[] }; health: { existing_condition_scenario?: string | null };
};
export type IntakeState = { profile: Profile; draft: Profile; version: number; draft_revision: number; draft_hash: string; health_consent: boolean;
  latest_run?: string | null; shortlist?: { plan_ids?: string[] };
  completeness: { ready: boolean; missing: { field: string; help: string }[]; answered: number; total: number; recommended: string[] } };
let capability = '';
try { capability = sessionStorage.getItem('helm-journey') || ''; } catch { /* In-memory session remains usable. */ }
export async function journey<T>(path: string, body?: unknown, method = body === undefined ? 'GET' : 'POST'): Promise<T> {
  const response = await fetch(`/api/journey${path}`, { method, credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Journey-Session': capability }, ...(body === undefined ? {} : { body: JSON.stringify(body) }) });
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || (typeof data.detail === 'string' ? data.detail : data.field_errors?.map((e: { message: string }) => e.message).join(' ')) || 'Please check your answers and try again.');
  return data as T;
}
export async function openJourney(reset = false): Promise<IntakeState> {
  if (reset) { capability = ''; try { sessionStorage.removeItem('helm-journey'); } catch { /* Optional storage. */ } }
  if (capability) return journey<IntakeState>('/profile');
  const data = await journey<IntakeState & { session_token: string }>('/sessions', {}, 'POST');
  capability = data.session_token;
  try { sessionStorage.setItem('helm-journey', capability); } catch { /* In-memory session remains usable. */ }
  return data;
}
export const money = (pence: number) => new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP' }).format(pence / 100);
export const pence = (value: string): number | null => /^\d+(\.\d{0,2})?$/.test(value) ? Number(value.split('.')[0])*100 + Number((value.split('.')[1] || '').padEnd(2, '0')) : null;
