import React, { Suspense, lazy } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Navigate, useLocation } from 'react-router-dom';
import { PublicApp } from './uk/PublicApp';

const CustomerApp = lazy(() => import('./CustomerApp'));

function Entry() {
  const { pathname } = useLocation();
  if (/^\/(?:app\/)?(?:broker|provider|staff)(?:\/|$)/.test(pathname)) return <Navigate to="/" replace/>;
  return pathname === '/login' || pathname === '/app' || pathname.startsWith('/app/') ? <CustomerApp/> : <PublicApp/>;
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode><BrowserRouter><Suspense fallback={<main style={{ padding: 40, fontFamily: 'system-ui' }} role="status">Loading Helm…</main>}><Entry/></Suspense></BrowserRouter></React.StrictMode>,
);
