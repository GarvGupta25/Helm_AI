import { Shell } from './Shell';
import { Home } from './Home';
import { About } from './About';
import { Route, Routes } from 'react-router-dom';
import { ContentPage, SEO } from './Content';
import { QuoteWizard } from './QuoteWizard';
import './quote.css';
import { Legal } from './Legal';
export function PublicApp() { return <Shell><SEO/><Routes><Route path="/" element={<Home/>}/><Route path="/about" element={<About/>}/><Route path="/get-cover/quote" element={<QuoteWizard/>}/><Route path="/legal/*" element={<Legal/>}/><Route path="*" element={<ContentPage/>}/></Routes></Shell>; }
