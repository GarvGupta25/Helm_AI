import { PressFeedback } from './ui/PressFeedback';
import './ui/apple-design.css';
import React, { Suspense, lazy } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Navigate, useLocation } from 'react-router-dom';
import { PublicApp } from './uk/PublicApp';

const MemberApp = lazy(() => import('./member/MemberApp'));
const CustomerApp = lazy(() => import('./CustomerApp'));
const Dashboard = lazy(() => import('./journey/Dashboard'));

function Entry() {
  const { pathname } = useLocation();
  if (pathname === '/login' || pathname === '/signup' || pathname === '/member' || pathname.startsWith('/member/')) return <MemberApp/>;
  if (pathname === '/quote-dashboard' || pathname === '/my-quotes') return <Dashboard/>;
  if (/^\/(?:app\/)?(?:broker|provider|staff)(?:\/|$)/.test(pathname)) return <Navigate to="/" replace/>;
  return pathname === '/login' || pathname === '/app' || pathname.startsWith('/app/') ? <CustomerApp/> : <PublicApp/>;
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode><PressFeedback/><BrowserRouter><Suspense fallback={<main style={{ padding: 40, fontFamily: 'system-ui' }} role="status">Loading Helm…</main>}><Entry/></Suspense></BrowserRouter></React.StrictMode>,
);
