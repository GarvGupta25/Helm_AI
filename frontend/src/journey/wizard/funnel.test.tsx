import { afterEach, expect, test, vi } from 'vitest';

afterEach(() => { vi.unstubAllEnvs(); vi.unstubAllGlobals(); localStorage.clear(); vi.resetModules(); });
test('analytics is inert without both the flag and explicit consent', async () => {
  const fetch = vi.fn().mockResolvedValue({}); vi.stubGlobal('fetch',fetch);
  vi.stubEnv('VITE_FUNNEL_ANALYTICS','false');
  const {track}=await import('./funnel');
  track('step_view','people'); expect(fetch).not.toHaveBeenCalled();
  vi.stubEnv('VITE_FUNNEL_ANALYTICS','true');
  track('step_view','people'); expect(fetch).not.toHaveBeenCalled();
  localStorage.setItem('helm-cookie-consent-v1',JSON.stringify({analytics:true}));
  track('step_view','people'); track('step_view','people');
  expect(fetch).toHaveBeenCalledTimes(1);
  const options=fetch.mock.calls[0][1];
  expect(options.credentials).toBe('omit');
  expect(JSON.parse(options.body)).toEqual({event:'step_view',step:'people',mode:'',choice:'',analytics_consent:true});
  localStorage.setItem('helm-cookie-consent-v1',JSON.stringify({analytics:false}));
  track('step_view','region'); expect(fetch).toHaveBeenCalledTimes(1);
});
