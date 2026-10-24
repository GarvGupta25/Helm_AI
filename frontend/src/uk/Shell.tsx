import { useEffect, useRef, useState, type ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import * as Navigation from '@radix-ui/react-navigation-menu';
import { ArrowUpRight, ChevronDown, Compass, Menu, Search } from 'lucide-react';
import { Action, Modal, Button, Eyebrow, useReducedMotion } from '../ui/primitives';
import { ukMarket } from '../market/uk.config';
import { audiences, coverPages, legalLinks, searchLinks } from './navigation';
import { ChatbotLauncher } from '../marketing/components/ChatbotLauncher';
import '../ui/uk.css';
import './site.css';

function Brand() { return <Link to="/" className="uk-brand" aria-label="Helm AI home"><Compass size={31} strokeWidth={1.3}/><span>helm<span className="uk-brand-ai">ai</span></span></Link>; }
function PublicAssistant() {
  const location=useLocation();const [mode,setMode]=useState(()=>{try{return sessionStorage.getItem('helm-wizard-mode');}catch{return null;}});
  useEffect(()=>{const update=()=>{try{setMode(sessionStorage.getItem('helm-wizard-mode'));}catch{setMode(null);}};window.addEventListener('helm-wizard-mode',update);return()=>window.removeEventListener('helm-wizard-mode',update);},[]);
  return import.meta.env.VITE_QUOTE_WIZARD==='true' && location.pathname.startsWith('/get-cover/quote') && mode==='chat'?null:<ChatbotLauncher/>;
}
function PanelLinks({ index, close }: { index: number; close?: () => void }) { const item = audiences[index]; return <>{item.groups.map(group => <div className="uk-menu-links" key={group.title}><strong>{group.title}</strong>{group.links.map(([text, to]) => <Link onClick={close} key={to} to={to}>{text}</Link>)}</div>)}</>; }
function Header() {
  const [scrolled, setScrolled] = useState(false); const [hidden, setHidden] = useState(false); const [menu, setMenu] = useState(false); const [search, setSearch] = useState(false); const [query, setQuery] = useState(''); const [nav, setNav] = useState('');
  const reduced = useReducedMotion(); const location = useLocation(); const touchY = useRef(0);
  useEffect(() => {
    let previous = Math.max(0, window.scrollY);
    let directionStart = previous;
    let direction = 0;
    const update = () => {
      const y = Math.max(0, window.scrollY);
      const nextDirection = Math.sign(y - previous);
      setScrolled(y > 80);
      if (nextDirection && nextDirection !== direction) {
        directionStart = previous;
        direction = nextDirection;
      }
      // Accumulate movement so small wheel/momentum events cannot flicker the header.
      if (y <= 180) setHidden(false);
      else if (Math.abs(y - directionStart) >= 24) setHidden(direction > 0);
      previous = y;
    };
    update();
    window.addEventListener('scroll', update, { passive: true });
    return () => window.removeEventListener('scroll', update);
  }, []);
  useEffect(() => { setMenu(false); setSearch(false); setNav(''); }, [location.pathname]);
  useEffect(() => { const key = (event: KeyboardEvent) => { if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); setSearch(true); } }; document.addEventListener('keydown', key); return () => document.removeEventListener('keydown', key); }, []);
  return <><a className="uk-skip" href="#uk-main">Skip to main content</a><div className="uk-demo">Demo — not a real insurance service <span>UK private medical cover · fictional plans</span></div><header className={`uk-header ${scrolled && !reduced ? 'pill' : ''} ${hidden && !nav && !reduced ? 'hidden' : ''}`}><Brand/><Navigation.Root className="uk-desktop-nav" delayDuration={120} skipDelayDuration={150} value={nav} onValueChange={setNav}><Navigation.List>{audiences.map((item, index) => <Navigation.Item key={item.path} value={item.path}><Navigation.Trigger>{item.name}<ChevronDown size={13}/></Navigation.Trigger><Navigation.Content className="uk-mega"><div className="uk-mega-feature"><Eyebrow>HELM FOR YOU</Eyebrow><h2>{item.title}</h2><Link to={item.path}>View all <span className="uk-arrow-circle"><ArrowUpRight size={22}/></span></Link></div><PanelLinks index={index}/><div className="uk-mega-promo"><Eyebrow>LET’S GET STARTED</Eyebrow><h3>{item.promo}</h3><p>{item.description}</p><Link to={item.destination}>{item.action} ↗</Link></div></Navigation.Content></Navigation.Item>)}</Navigation.List></Navigation.Root><div className="uk-header-actions"><button className="uk-icon" aria-label="Search website" onClick={() => setSearch(true)}><Search size={19}/></button><details className="uk-login"><summary>Log in <ChevronDown size={13}/></summary><div><span className="uk-login-label">YOUR HELM ACCOUNT</span><Link to="/signup">Create an account <ArrowUpRight size={15}/></Link><Link to="/login">Member log in <ArrowUpRight size={15}/></Link></div></details><Link className="uk-header-cta" to="/get-cover/quote">Get a quote <ArrowUpRight size={17}/></Link><button className="uk-icon uk-mobile-menu" aria-label="Open navigation" onClick={() => setMenu(true)}><Menu/></button></div></header>
  <Modal open={menu} onClose={() => setMenu(false)} title="Explore Helm"><div onTouchStart={event => { touchY.current = event.touches[0].clientY; }} onTouchEnd={event => { if (event.changedTouches[0].clientY - touchY.current > 120) setMenu(false); }}>{audiences.map((item, index) => <details className="uk-accordion" key={item.path}><summary>{item.name}</summary><PanelLinks index={index} close={() => setMenu(false)}/><Link to={item.path}>View all ↗</Link></details>)}<div className="uk-actions"><Action to="/get-cover/quote">Get a quote</Action><Link to="/signup">Create an account</Link><Link to="/login">Member log in</Link></div></div></Modal>
  <Modal open={search} onClose={() => setSearch(false)} title="What can we help you find?"><label className="uk-field">Search pages, guides and FAQs<input autoFocus value={query} onChange={event => setQuery(event.target.value)} placeholder="Try underwriting or claims"/></label><div className="uk-search-results">{searchLinks.filter(([text]) => text.toLowerCase().includes(query.toLowerCase())).filter(([text], i, list) => list.findIndex(x => x[0] === text) === i).slice(0, 12).map(([text, to]) => <Link to={to} key={`${text}-${to}`} onClick={() => setSearch(false)}>{text}<ArrowUpRight size={16}/></Link>)}</div><small>Ctrl / ⌘ K opens search.</small></Modal></>;
}

export function Shell({ children }: { children: ReactNode }) {
  const [external, setExternal] = useState<URL | null>(null); const [cookieOpen, setCookieOpen] = useState(() => { try { return !localStorage.getItem('helm-cookie-consent-v1'); } catch { return true; } }); const [analytics, setAnalytics] = useState(false); const [marketing, setMarketing] = useState(false); const location = useLocation();
  useEffect(() => { document.documentElement.lang = 'en-GB'; const handler = (event: MouseEvent) => { const anchor = event.target instanceof Element ? event.target.closest('a') : null; if (!anchor || !/^https?:/.test(anchor.href)) return; const url = new URL(anchor.href); if (url.origin !== window.location.origin) { event.preventDefault(); setExternal(url); } }; document.addEventListener('click', handler); return () => document.removeEventListener('click', handler); }, []);
  useEffect(() => { window.scrollTo(0, 0); }, [location.pathname]);
  function consent(a: boolean, m: boolean) { const value = { necessary: true, analytics: a, marketing: m, version: '1', at: new Date().toISOString() }; try { localStorage.setItem('helm-cookie-consent-v1', JSON.stringify(value)); } catch { /* Preferences remain in memory when storage is disabled. */ } setCookieOpen(false); setAnalytics(a); setMarketing(m); }
  const columns = [{ name: 'Shop', links: [['Get cover', '/get-cover'], ['Compare plans', '/get-cover/compare'], ['Find care', '/find-care'], ['Glossary', '/glossary']] }, { name: 'Members', links: [['Log in', '/login'], ['Make a claim', '/members/claims'], ['Your adviser', '/contact'], ['Virtual GP & extras', '/members/perks'], ['Helm app', '/members/app']] }, { name: 'Cover for you', links: coverPages.map(([name, slug]) => [name, `/cover-for-you/${slug}`]) }, { name: 'Partners', links: [['Business', '/business'], ['Advisers', '/advisers'], ['Insurers', '/insurers']] }, { name: 'About', links: [['About Helm', '/about'], ['Guides', '/guides'], ['Press', '/about/press'], ['Careers', '/about/careers']] }];
  return <div className="uk-site"><Header/><main id="uk-main" tabIndex={-1}>{children}</main><footer className="uk-footer"><div className="uk-footer-top"><Brand/><div><Eyebrow>A LITTLE CLARITY GOES A LONG WAY.</Eyebrow><h2>Cover, with <em>confidence.</em></h2></div><Action to="/contact">Talk to an adviser</Action></div><div className="uk-footer-columns">{columns.map(column => <div key={column.name}><h3>{column.name}</h3>{column.links.map(([text, to]) => <Link to={to} key={to}>{text}</Link>)}</div>)}<div><h3>Need help?</h3><p>{ukMarket.phone}<br/>Mon–Fri 08:00–20:00<br/>(Europe/London)</p><small>Demo contact number.<br/>Use the contact page for details.</small></div></div><div className="uk-legal-links">{legalLinks.map(([text, to]) => <Link to={to} key={to}>{text}</Link>)}<button onClick={() => setCookieOpen(true)}>Cookie settings</button></div><p className="uk-regulatory">{ukMarket.firmName} · FRN {ukMarket.frn} · Company {ukMarket.companyNumber} · ICO {ukMarket.icoNumber} · {ukMarket.address}. Regulatory details are unresolved. This demonstration makes no claim of FCA authorisation. Plans are fictional; no cover is sold. <a href="https://register.fca.org.uk/">Check a real firm on the FCA Register ↗</a></p><div className="uk-copyright"><span>© {new Date().getFullYear()} Helm AI</span><span>United Kingdom · English</span><span>Thoughtfully simple.</span></div></footer><PublicAssistant/>
  <Modal open={!!external} onClose={() => setExternal(null)} title="You’re leaving Helm"><p>You’re about to visit <strong>{external?.hostname}</strong>, which isn’t run by Helm. We’re not responsible for its content or privacy practices.</p><div className="uk-actions"><Button variant="secondary" onClick={() => setExternal(null)}>Go back</Button><Button onClick={() => { if (external) window.open(external.href, '_blank', 'noopener,noreferrer'); setExternal(null); }}>Continue</Button></div></Modal>
  <Modal open={cookieOpen} onClose={() => consent(false, false)} title="Your privacy. Your choice."><p>Essential storage keeps this site working. Optional analytics and marketing stay off unless you choose them. This demo loads no analytics or advertising scripts.</p><label className="uk-check"><input type="checkbox" checked disabled/>Essential (always on)</label><label className="uk-check"><input type="checkbox" checked={analytics} onChange={event => setAnalytics(event.target.checked)}/>Analytics</label><label className="uk-check"><input type="checkbox" checked={marketing} onChange={event => setMarketing(event.target.checked)}/>Marketing</label><div className="uk-actions"><Button onClick={() => consent(false, false)}>Reject all</Button><Button onClick={() => consent(true, true)}>Accept all</Button><Button variant="secondary" onClick={() => consent(analytics, marketing)}>Save choices</Button></div><Link to="/legal/cookies" onClick={() => setCookieOpen(false)}>Read the cookie policy</Link></Modal></div>;
}
