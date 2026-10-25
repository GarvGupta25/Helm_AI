import { describe, expect, it } from 'vitest';
import type { Profile } from '../api';
import { formatDate, household, mustHaves, planName, profileHeadline, wholeMoney } from './checkoutPresentation';

const profile: Profile = { people: [{ relationship: 'lead_adult', age_years: 35 }], location: { region: 'London' }, cover: { start_date: '2026-10-25', underwriting_required: false }, budget: { choice: 'no_target', monthly_pence: null, strict: false }, excess: { choice: 'amount', max_pence: 25000, strict: true }, hospital_list: { choice: 'minimum_tier', minimum_tier: 1 }, outpatient: { minimum_annual_pence: null, required: false }, benefits: { required: [], preferred: [] }, health: {} };

describe('checkout display preserves canonical meaning', () => {
  it('pluralizes people and hides zero counts', () => {
    expect(household(profile)).toBe('1 adult');
    expect(household({ ...profile, people: [...profile.people, { relationship: 'partner', age_years: 32 }, { relationship: 'child', age_years: 0 }, { relationship: 'child', age_years: 4 }] })).toBe('2 adults, 2 children');
  });
  it('formats calendar dates without local-time shifts', () => {
    expect(formatDate('2026-10-25')).toBe('25 Oct 2026');
    expect(formatDate(null)).toBe('Not answered');
    expect(formatDate('invalid')).toBe('Not answered');
    expect(profileHeadline(profile)).toBe('1 adult, London. Starts 25 Oct 2026.');
  });
  it('keeps pence accurate while removing unnecessary whole-pound decimals', () => {
    expect(wholeMoney(25000)).toBe('£250');
    expect(wholeMoney(9586)).toBe('£95.86');
    expect(wholeMoney(0)).toBe('£0');
  });
  it('uses a readable name without inventing benefits or changing canonical names', () => {
    expect(planName('Research 8 / Tier 4 / List 2 / Excess £250')).toBe('Health plan 8');
    expect(planName('Existing product name')).toBe('Existing product name');
  });
  it('explains every hard requirement, including zero-valued limits', () => {
    expect(mustHaves(profile)).toEqual(['excess up to £250', 'standard hospital access (demo)']);
    expect(mustHaves({ ...profile, budget: { choice: 'amount', monthly_pence: 0, strict: true }, excess: { choice: 'amount', max_pence: 0, strict: true }, benefits: { required: ['mental_health'], preferred: [] } })).toContain('budget up to £0 a month');
    expect(mustHaves(profile)).not.toContain('No limit set');
  });
});
