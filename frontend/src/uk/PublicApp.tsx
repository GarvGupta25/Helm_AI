import { Shell } from './Shell';
import { lazy, Suspense } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { ContentPage, SEO } from './Content';
import { Skeleton } from '../ui/primitives';
import './quote.css';
import './hardening.css';
const Home = lazy(() => import('./Home').then(module => ({ default: module.Home })));
const About = lazy(() => import('./About').then(module => ({ default: module.About })));
const Research = lazy(() => import('./Research').then(module => ({ default: module.Research })));
const Intake = lazy(() => import('../journey/Intake'));
const Wizard = lazy(() => import('../journey/wizard/WizardApp'));
const Plans = lazy(() => import('../journey/wizard/PlansApp'));
const Verification = lazy(() => import('../journey/wizard/Verification'));
const AccessChoice = lazy(() => import('../journey/wizard/AccessChoice'));
const quoteWizard = import.meta.env.VITE_QUOTE_WIZARD === 'true';
const Legal = lazy(() => import('./Legal').then(module => ({ default: module.Legal })));
export function PublicApp() { return <Shell><SEO/><Suspense fallback={<section className="uk-section" style={{ minHeight: 'calc(100svh - 125px)' }}><Skeleton/></section>}><Routes><Route path="/" element={<Home/>}/><Route path="/get-cover/compare" element={quoteWizard?<Plans/>:<Navigate to="/get-cover/quote" replace/>}/><Route path="/get-cover/plans/*" element={quoteWizard?<Plans/>:<Navigate to="/get-cover/quote" replace/>}/><Route path="/get-cover/selection" element={quoteWizard?<Plans/>:<Navigate to="/get-cover/quote" replace/>}/><Route path="/get-cover/verify/*" element={quoteWizard?<Verification/>:<Navigate to="/get-cover/quote" replace/>}/><Route path="/get-cover/access" element={quoteWizard?<AccessChoice/>:<Navigate to="/get-cover/quote" replace/>}/><Route path="/research" element={<Navigate to="/get-cover/quote" replace/>}/><Route path="/about" element={<About/>}/><Route path="/get-cover/quote/*" element={quoteWizard ? <Wizard/> : <Intake/>}/><Route path="/get-cover/legacy-intake" element={<Intake/>}/><Route path="/get-cover/legacy-demo" element={<Research/>}/><Route path="/legal/*" element={<Legal/>}/><Route path="*" element={<ContentPage/>}/></Routes></Suspense></Shell>; }
