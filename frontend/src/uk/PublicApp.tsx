import { Shell } from './Shell';
import { lazy, Suspense } from 'react';
import { Route, Routes } from 'react-router-dom';
import { ContentPage, SEO } from './Content';
import { Skeleton } from '../ui/primitives';
import './quote.css';
import './hardening.css';
const Home = lazy(() => import('./Home').then(module => ({ default: module.Home })));
const About = lazy(() => import('./About').then(module => ({ default: module.About })));
const QuoteWizard = lazy(() => import('./QuoteWizard').then(module => ({ default: module.QuoteWizard })));
const Legal = lazy(() => import('./Legal').then(module => ({ default: module.Legal })));
export function PublicApp() { return <Shell><SEO/><Suspense fallback={<section className="uk-section" style={{ minHeight: 'calc(100svh - 125px)' }}><Skeleton/></section>}><Routes><Route path="/" element={<Home/>}/><Route path="/about" element={<About/>}/><Route path="/get-cover/quote" element={<QuoteWizard/>}/><Route path="/legal/*" element={<Legal/>}/><Route path="*" element={<ContentPage/>}/></Routes></Suspense></Shell>; }
