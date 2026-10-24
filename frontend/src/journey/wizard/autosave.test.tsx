import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import * as api from '../api';
import type { IntakeState, Profile } from '../api';
import { useWizardProfile } from './useWizardProfile';

afterEach(()=>vi.restoreAllMocks());
it('accepts server-normalised defaults instead of resaving forever',async()=>{
 const profile:Profile={people:[],location:{region:null},cover:{start_date:null,underwriting_required:false},budget:{choice:null,monthly_pence:null,strict:false},excess:{choice:null,max_pence:null,strict:false},hospital_list:{choice:null,minimum_tier:null},outpatient:{minimum_annual_pence:null,required:false},benefits:{required:null,preferred:[]},health:{}};
 const initial:IntakeState={profile,draft:profile,version:0,draft_revision:0,draft_hash:'initial',health_consent:false,completeness:{ready:false,answered:0,total:7,missing:[],recommended:[]}};
 vi.spyOn(api,'openJourney').mockResolvedValue(initial);
 const save=vi.spyOn(api,'journey').mockImplementation(async(_path,body)=>{
  const draft=(body as {profile:Profile}).profile;
  return {...initial,draft:{...draft,people:draft.people.map(p=>({...p,date_of_birth:null,smoker_status:null}))},draft_revision:1,draft_hash:'saved'} as never;
 });
 const {result,unmount}=renderHook(()=>useWizardProfile());await waitFor(()=>expect(result.current.state).toBeDefined());
 act(()=>result.current.change('people',[{relationship:'lead_adult',age_years:35}]));
 await act(async()=>{await result.current.flush();});
 expect(save).toHaveBeenCalledTimes(1);expect(result.current.saved).toBe(true);expect(result.current.saving).toBe(false);expect(result.current.draft?.people[0].age_years).toBe(35);unmount();
});
