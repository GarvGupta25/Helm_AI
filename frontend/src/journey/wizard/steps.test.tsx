import { describe, expect, it } from 'vitest';
import type { Profile } from '../api';
import { benefitGroups, firstMissing, guardedStep, localDate, problem, steps } from './steps';

export const empty: Profile = {people:[],location:{region:null},cover:{start_date:null,underwriting_required:false},budget:{choice:null,monthly_pence:null,strict:false},excess:{choice:null,max_pence:null,strict:false},hospital_list:{choice:null,minimum_tier:null},outpatient:{minimum_annual_pence:null,required:false},benefits:{required:null,preferred:[]},health:{}};
describe('wizard registry matches the canonical contract',()=>{
  it('guards deep links at the first missing mandatory topic',()=>{
    expect(guardedStep('review',empty)).toBe('people');
    const complete={...empty,people:[{relationship:'lead_adult' as const,age_years:35}],location:{region:'England'},cover:{...empty.cover,start_date:localDate()},budget:{...empty.budget,choice:'no_target'},excess:{...empty.excess,choice:'no_preference'},hospital_list:{choice:'no_preference',minimum_tier:null},benefits:{required:[],preferred:[]}};
    expect(firstMissing(complete)).toBeUndefined(); expect(guardedStep('review',complete)).toBeUndefined();
    expect(problem('people',{...complete,people:[{relationship:'lead_adult',age_years:17}]})).toMatch('18–85');
    expect(problem('budget',{...complete,budget:{choice:'amount',monthly_pence:null,strict:false}})).toMatch('budget');
  });
  it('has unique routes, every existing benefit and explicit none vs unanswered',()=>{
    expect(new Set(steps.map(s=>s.id)).size).toBe(steps.length);
    expect(Object.values(benefitGroups).flat()).toHaveLength(11);
    expect(problem('benefits/everyday',empty)).toBeTruthy();
    expect(problem('benefits/everyday',{...empty,benefits:{required:[],preferred:[]}})).toBe('');
    expect(problem('optional/underwriting',{...empty,cover:{...empty.cover,underwriting_required:true}})).toBeTruthy();
    expect(problem('optional/postcode',{...empty,location:{region:null,postcode:'wrong'}})).toBeTruthy();
  });
});
