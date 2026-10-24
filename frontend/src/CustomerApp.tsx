import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Link, NavLink, Navigate, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import type { Session } from '@supabase/supabase-js';
import { Compass, ArrowUpRight, ArrowRight, Mic, ShieldCheck, Layers3, LayoutDashboard, LogOut, Menu, Check, Sparkles, ClipboardCheck, Bell } from 'lucide-react';
import { api, auth, configureAuth, type Config, aed } from './api';
import { Loading, ErrorView } from './Feedback';
import './styles.css';
import { MarketingLayout } from './marketing/components/MarketingLayout';
import './foundation.css';

const HomePage = React.lazy(() => import('./marketing/pages/HomePage').then(module => ({ default: module.HomePage })));
const AboutPage = React.lazy(() => import('./marketing/pages/AboutPage').then(module => ({ default: module.AboutPage })));
const PartnersPage = React.lazy(() => import('./marketing/pages/PartnersPage').then(module => ({ default: module.PartnersPage })));
const PlansPage = React.lazy(() => import('./marketing/pages/PlansPage').then(module => ({ default: module.PlansPage })));
const PlanDetailPage = React.lazy(() => import('./marketing/pages/PlanDetailPage').then(module => ({ default: module.PlanDetailPage })));
const GuidePage = React.lazy(() => import('./marketing/pages/GuidePage').then(module => ({ default: module.GuidePage })));
const GuideTopicPage = React.lazy(() => import('./marketing/pages/GuideTopicPage').then(module => ({ default: module.GuideTopicPage })));
const HowItWorksPage = React.lazy(() => import('./marketing/pages/HowItWorksPage').then(module => ({ default: module.HowItWorksPage })));
const FaqPage = React.lazy(() => import('./marketing/pages/FaqPage').then(module => ({ default: module.FaqPage })));
const ClaimsExplainedPage = React.lazy(() => import('./marketing/pages/ClaimsExplainedPage').then(module => ({ default: module.ClaimsExplainedPage })));
const ContactPage = React.lazy(() => import('./marketing/pages/ContactPage').then(module => ({ default: module.ContactPage })));
const PrivacyPage = React.lazy(() => import('./marketing/pages/PrivacyPage').then(module => ({ default: module.PrivacyPage })));
const TermsPage = React.lazy(() => import('./marketing/pages/TermsPage').then(module => ({ default: module.TermsPage })));
const DisclaimerPage = React.lazy(() => import('./marketing/pages/DisclaimerPage').then(module => ({ default: module.DisclaimerPage })));

const Dashboard = React.lazy(() => import('./Shopping').then(module => ({ default: module.Dashboard })));
const Intake = React.lazy(() => import('./Shopping').then(module => ({ default: module.Intake })));
const QuotePage = React.lazy(() => import('./Shopping').then(module => ({ default: module.QuotePage })));
const ApplicationPage = React.lazy(() => import('./Shopping').then(module => ({ default: module.ApplicationPage })));
const PolicyPage = React.lazy(() => import('./Shopping').then(module => ({ default: module.PolicyPage })));
const MarketplaceJourney = React.lazy(() => import('./MarketplaceJourney').then(module => ({ default: module.MarketplaceJourney })));

const client = new QueryClient({ defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } } });

function Brand() { return <Link to="/" className="brand" aria-label="Helm AI home"><span><Compass size={25}/></span>helm<span className="brand-ai">ai</span></Link>; }
function Login({ session, config }: { session: Session | null; config: Config }) {
  const [mode, setMode] = useState<'login' | 'signup' | 'recover' | 'reset'>(location.pathname === '/signup' ? 'signup' : 'login'); const [message, setMessage] = useState(''); const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  useEffect(() => { if (new URLSearchParams(location.search).has('recovery')) setMode('reset'); }, []);
  if (session && mode !== 'reset' && !new URLSearchParams(location.search).has('recovery')) return <Navigate to="/app" replace/>;
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!auth) return; setBusy(true); setMessage(''); const values = new FormData(event.currentTarget);
    const email = String(values.get('email') || ''); const password = String(values.get('password') || '');
    try {
      if (mode === 'recover') { const { error } = await auth.auth.resetPasswordForEmail(email, { redirectTo: location.origin + '/login?recovery=1' }); if (error) throw error; setMessage('If this account exists, a recovery link has been sent.'); }
      else if (mode === 'reset') { const { error } = await auth.auth.updateUser({ password }); if (error) throw error; navigate('/app'); }
      else if (mode === 'signup') { const { data, error } = await auth.auth.signUp({ email, password, options: { data: { full_name: String(values.get('name') || '').trim() }, emailRedirectTo: location.origin + '/app' } }); if (error) throw error; if (!data.session) setMessage('Check your email to verify your account, then sign in.'); else navigate('/app'); }
      else { const { error } = await auth.auth.signInWithPassword({ email, password }); if (error) throw error; navigate('/app'); }
    } catch (e) { setMessage((e as Error).message); } finally { setBusy(false); }
  }
  return <div className="auth-page"><div className="auth-story"><Brand/><span className="eyebrow">A CLEARER WAY TO FIND COVER</span><h1>Your needs.<br/>Your choices.<br/><span>All connected.</span></h1><p>A little understanding goes a long way.<br/>Let’s find where your cover should start.</p><span className="badge light">Fictional insurance demonstration</span></div><main className="auth-panel"><Link className="text-link" to="/">← Back to Helm</Link><div className="auth-form"><span className="eyebrow">WELCOME TO HELM</span><h2>{mode === 'signup' ? 'Make yourself at home.' : mode === 'recover' ? 'Find your way back.' : mode === 'reset' ? 'Choose a new password.' : 'Good to see you.'}</h2><p>{mode === 'login' ? 'Sign in to pick up where you left off.' : 'Your profile will be saved with your account.'}</p>
    {!config.auth_configured && <div className="notice">Account access is not configured yet. Connect local or hosted Supabase to enable sign-in and saved profiles.</div>}
    <form onSubmit={submit}>{mode === 'signup' && <label className="field">Full name<input name="name" autoComplete="name" required maxLength={100} placeholder="Your name"/></label>}{mode !== 'reset' && <label className="field">Email address<input name="email" type="email" autoComplete="email" required placeholder="you@example.com"/></label>}{mode !== 'recover' && <label className="field">Password<input name="password" type="password" minLength={8} autoComplete={mode === 'login' ? 'current-password' : 'new-password'} required placeholder="At least 8 characters"/></label>}<button disabled={busy || !config.auth_configured}>{busy ? 'Please wait…' : mode === 'signup' ? 'Create account' : mode === 'recover' ? 'Send recovery link' : mode === 'reset' ? 'Update password' : 'Sign in'}<ArrowRight size={17}/></button></form>
    {message && <p className="notice" role="status">{message}</p>}<div className="auth-links"><button className="quiet" onClick={() => { setMessage(''); setMode(mode === 'signup' ? 'login' : 'signup'); }}>{mode === 'signup' ? 'Already have an account? Sign in' : 'New here? Create an account'}</button><button className="quiet" onClick={() => { setMessage(''); setMode('recover'); }}>Forgot password?</button></div><small>Passwords stay in the sign-in flow. Never share passwords, card details or one-time codes with the assistant.</small></div></main></div>;
}

function PoliciesLink({ onClick }: { onClick: () => void }) {
  const policies = useQuery<any[]>({ queryKey: ['policies'], queryFn: () => api('/api/policies') });
  const policy = policies.data?.find(item => item.status === 'demo_active') || policies.data?.[0];
  return <NavLink to={policy ? `/app/policies/${policy.id}` : '/app'} onClick={onClick}><ShieldCheck size={19}/> Policies & cover</NavLink>;
}

function PortalNotice({ role, onSignOut }: { role: string; onSignOut: () => Promise<void> }) {
  const portals: Record<string, { name: string; url: string | undefined }> = {
    broker: { name: 'Broker', url: import.meta.env.VITE_BROKER_PORTAL_URL },
    provider: { name: 'Provider', url: import.meta.env.VITE_PROVIDER_PORTAL_URL },
    staff: { name: 'Staff', url: import.meta.env.VITE_STAFF_PORTAL_URL },
    admin: { name: 'Staff', url: import.meta.env.VITE_STAFF_PORTAL_URL },
  };
  const portal = portals[role] || { name: 'Professional', url: undefined };
  let portalUrl: string | undefined;
  try {
    const url = new URL(portal.url?.trim() || '');
    if (url.protocol === 'https:' || url.protocol === 'http:') portalUrl = url.href;
  } catch { /* An unset or invalid placeholder must not become a broken link. */ }
  return <main className="startup-error"><Brand/><h1>Please use the {portal.name} portal.</h1><p>This website provides customer insurance accounts. Use your organisation's portal for professional work.</p>{portalUrl ? <p><a className="button" href={portalUrl}>Open {portal.name} portal <ArrowUpRight size={17}/></a></p> : <p>The portal address has not been configured. Contact your organisation for the correct address.</p>}<button className="secondary" onClick={() => { void onSignOut(); }}>Sign out</button></main>;
}

function Shell({ session }: { session: Session | null }) {
  const [signingOut, setSigningOut] = useState(false);
  const [open, setOpen] = useState(false); const [notificationsOpen, setNotificationsOpen] = useState(false); const navigate = useNavigate();
  const access = useQuery({ queryKey: ['access', session?.user.id], queryFn: () => api<{ role: 'member' | 'broker' | 'provider' }>('/api/me/access'), enabled: !!session });
  const notifications = useQuery<any[]>({ queryKey: ['marketplace-notifications'], queryFn: () => api('/api/marketplace/notifications'), enabled: access.data?.role === 'member', refetchInterval: 5000 });
  useEffect(() => {
    function dismiss(event: KeyboardEvent) {
      if (event.key === 'Escape') { setOpen(false); setNotificationsOpen(false); }
    }
    function outside(event: PointerEvent) {
      if (event.target instanceof Element && !event.target.closest('.notification-menu')) setNotificationsOpen(false);
    }
    document.addEventListener('keydown', dismiss);
    document.addEventListener('pointerdown', outside);
    return () => { document.removeEventListener('keydown', dismiss); document.removeEventListener('pointerdown', outside); };
  }, []);
  if (!session) return signingOut ? <Loading/> : <Navigate to="/login" replace/>;
  async function logout() {
    setSigningOut(true);
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    try {
      await auth?.auth.signOut();
    } catch {
      // A temporary local Auth outage must not trap a user in an old browser session.
      await auth?.auth.signOut({ scope: 'local' });
    } finally {
      client.clear();
      // Clearing the query cache remounts auth-dependent routes. Leave that router
      // with a document navigation so its stale auth redirect cannot win the race.
      window.location.replace('/');
    }
  }
  if (access.isPending) return <Loading/>;
  if (access.error) return <main className="startup-error"><Brand/><h1>We could not check your account access.</h1><ErrorView error={access.error}/><div className="actions"><button onClick={() => { void access.refetch(); }}>Try again</button><button className="secondary" onClick={() => { void logout(); }}>Sign out</button></div></main>;
  if (access.data?.role !== 'member') return <PortalNotice role={access.data?.role || ''} onSignOut={logout}/>;
  return <div className="app-shell"><a className="skip-link" href="#workspace">Skip to workspace</a><aside className={`sidebar ${open ? 'open' : ''}`}><Brand/><button className="quiet navigation-dismiss" onClick={() => setOpen(false)}>Close navigation</button><span className="nav-caption">YOUR WORKSPACE</span><nav><NavLink end to="/app" onClick={() => setOpen(false)}><LayoutDashboard size={19}/> Overview</NavLink><PoliciesLink onClick={() => setOpen(false)}/><Link to="/faq"><MessageIcon/> About this demo</Link></nav><div className="sidebar-bottom"><div className="sidebar-note"><ShieldCheck size={22}/><strong>Clarity, not guesswork.</strong><p>Your choices stay yours. Review the details before every submission.</p></div><button className="quiet" onClick={logout}><LogOut size={17}/> Sign out</button></div></aside><div className="app-content"><header className="workspace-header"><button className="mobile-menu quiet" onClick={() => setOpen(!open)} aria-label="Toggle navigation" aria-expanded={open}><Menu size={23}/></button><span>Individual health insurance <span className="header-divider">/</span> UAE</span><div><span className="badge neutral">Demo workspace</span>{access.data?.role === 'member' && <div className="notification-menu"><button className="quiet notification-bell" onClick={() => setNotificationsOpen(value => !value)} aria-label="Marketplace notifications" aria-expanded={notificationsOpen}><Bell size={19}/>{notifications.data?.length ? <span>{notifications.data.length}</span> : null}</button>{notificationsOpen && <div className="notification-popover">{notifications.data?.length ? notifications.data.map((item, index) => <Link to={`/app/marketplace/${item.case_id}`} onClick={() => setNotificationsOpen(false)} key={`${item.case_id}-${item.provider}-${index}`}><strong>{item.provider}</strong><small>{item.message}</small></Link>) : <p>No marketplace updates yet.</p>}</div>}</div>}<span className="user-avatar" title={session.user.email}>{session.user.email?.[0]?.toUpperCase() || 'H'}</span></div></header><main id="workspace"><Outlet/></main><footer className="workspace-footer">Helm AI · All insurance products and transactions in this workspace are demonstrations.</footer></div></div>;
}
function MessageIcon() { return <Layers3 size={19}/>; }
function App() {
  const location = useLocation();
  const config = useQuery({ queryKey: ['config'], queryFn: () => api<Config>('/api/config') }); const [session, setSession] = useState<Session | null>(null); const [ready, setReady] = useState(false);
  useEffect(() => {
    if (!config.data) return; configureAuth(config.data);
    if (!auth) { setReady(true); return; }
    let active = true; void auth.auth.getSession().then(({ data }) => { if (active) { setSession(data.session); setReady(true); } });
    const { data: subscription } = auth.auth.onAuthStateChange((_event, next) => { setSession(next); setReady(true); });
    return () => { active = false; subscription.subscription.unsubscribe(); };
  }, [config.data]);
  if (config.error) return <div className="startup-error"><Brand/><h1>The workspace service is unavailable.</h1><p>Start the Helm API, then reload this page.</p><ErrorView error={config.error}/><button onClick={() => { void config.refetch(); }}>Try again</button></div>;
  if (!config.data || !ready) return <Loading/>;
  return <React.Suspense fallback={<Loading/>}><Routes>
    {/* Marketing site — public, wrapped in MarketingLayout (header + footer) */}
    <Route element={<MarketingLayout />}>
      <Route path="/" element={<HomePage />} />
      <Route path="/about" element={<AboutPage />} />
      <Route path="/partners" element={<PartnersPage />} />
      <Route path="/plans" element={<PlansPage />} />
      <Route path="/plans/:planId" element={<PlanDetailPage />} />
      <Route path="/guide" element={<GuidePage />} />
      <Route path="/guide/:topicSlug" element={<GuideTopicPage />} />
      <Route path="/how-it-works" element={<HowItWorksPage />} />
      <Route path="/faq" element={<FaqPage />} />
      <Route path="/claims-explained" element={<ClaimsExplainedPage />} />
      <Route path="/contact" element={<ContactPage />} />
      <Route path="/legal/privacy" element={<PrivacyPage />} />
      <Route path="/legal/terms" element={<TermsPage />} />
      <Route path="/legal/disclaimer" element={<DisclaimerPage />} />
    </Route>

    {/* Customer account */}
    <Route path="/login" element={<Login session={session} config={config.data}/>} /><Route path="/signup" element={<Login session={session} config={config.data}/>} />
    <Route path="/app" element={<Shell session={session}/>}>
      <Route index element={<Dashboard/>} />
      <Route path="intake/:caseId" element={<Intake config={config.data}/>} />
      <Route path="quotes/:quoteId" element={<QuotePage/>} />
      <Route path="applications/:applicationId" element={<ApplicationPage/>} />
      <Route path="marketplace/:caseId" element={<MarketplaceJourney/>} />
      <Route path="policies/:policyId" element={<PolicyPage config={config.data}/>} />
    </Route>

    <Route path="*" element={<Navigate to="/" replace/>} />
  </Routes></React.Suspense>;
}
export default function CustomerApp() { return <QueryClientProvider client={client}><App/></QueryClientProvider>; }
