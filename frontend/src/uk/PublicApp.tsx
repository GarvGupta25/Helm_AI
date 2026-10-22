import { Shell } from './Shell';
import { Home } from './Home';
import { About } from './About';
import { Route, Routes } from 'react-router-dom';
export function PublicApp() { return <Shell><Routes><Route path="/about" element={<About/>}/><Route path="*" element={<Home/>}/></Routes></Shell>; }
