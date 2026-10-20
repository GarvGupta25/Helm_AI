import { useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { MarketingHeader } from './MarketingHeader';
import { MarketingFooter } from './MarketingFooter';
import { ChatbotLauncher } from './ChatbotLauncher';
import '../tokens.css';
import '../marketing.css';
import './MarketingLayout.css';
export function MarketingLayout() {
  const { pathname, hash } = useLocation();
  useEffect(() => { if (!hash) window.scrollTo({ top: 0, behavior: 'instant' }); }, [pathname, hash]);
  return <div className="marketing-layout"><a className="skip-link" href="#public-content">Skip to content</a><MarketingHeader key={pathname}/><main id="public-content" className="marketing-layout__main"><Outlet /></main><MarketingFooter /><ChatbotLauncher /></div>;
}
