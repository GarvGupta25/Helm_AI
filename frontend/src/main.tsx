import React, { Suspense, lazy } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

const PublicApp = lazy(() => import('./uk/PublicApp').then(module => ({ default: module.PublicApp })));
const CustomerApp = lazy(() => import('./CustomerApp'));

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode><BrowserRouter><Suspense fallback={<main style={{ padding: 40, fontFamily: 'system-ui' }} role="status">Loading Helm…</main>}><Routes>
    {['/app/broker/*', '/app/provider/*', '/app/staff/*', '/broker/*', '/provider/*', '/staff/*'].map(path => <Route key={path} path={path} element={<Navigate to="/" replace/>}/>)}
    <Route path="/app/*" element={<CustomerApp/>}/>
    <Route path="/login" element={<CustomerApp/>}/>
    <Route path="*" element={<PublicApp/>}/>
  </Routes></Suspense></BrowserRouter></React.StrictMode>,
);
