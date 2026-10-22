import { Shell } from './Shell';
import { Home } from './Home';
import { About } from './About';
import { Route, Routes } from 'react-router-dom';
import { ContentPage, SEO } from './Content';
export function PublicApp() { return <Shell><SEO/><Routes><Route path="/" element={<Home/>}/><Route path="/about" element={<About/>}/><Route path="*" element={<ContentPage/>}/></Routes></Shell>; }
