import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeTracker } from './features/theme-tracker/pages/ThemeTracker';
import { Dashboard } from './features/analyzer/pages/Dashboard';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ThemeTracker />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  );
}
