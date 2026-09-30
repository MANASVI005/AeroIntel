import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { SplashIntro } from './components/SplashIntro';
import { DashboardPlaceholder } from './pages/DashboardPlaceholder';
import { MobileCapturePage } from './pages/MobileCapturePage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        {/* Initial 5-second Splash / Intro screen */}
        <Route path="/" element={<SplashIntro targetRoute="/dashboard" />} />
        
        {/* Destination Dashboard placeholder page */}
        <Route path="/dashboard" element={<DashboardPlaceholder />} />

        {/* Dedicated Mobile Technician Camera Capture View */}
        <Route path="/mobile" element={<MobileCapturePage />} />

        {/* Catch-all redirects back to intro */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
