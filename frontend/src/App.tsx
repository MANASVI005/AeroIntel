import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Landing from './pages/Landing';
import Dashboard from './pages/Dashboard';
import NewInspection from './pages/NewInspection';
import InspectionResult from './pages/InspectionResult';
import InspectionHistory from './pages/InspectionHistory';
import AeroMemory from './pages/AeroMemory';
import Reports from './pages/Reports';
import InspectionReport from './pages/InspectionReport';
import ModelPerformance from './pages/ModelPerformance';
import Settings from './pages/Settings';
import { MobileCapturePage } from './pages/MobileCapturePage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public landing — hero with 3D rotating aircraft + dashboard section */}
        <Route path="/" element={<Landing />} />

        {/* In-app shell routes (screens built one-by-one in Stage 1) */}
        {/* Dashboard — real screen (Step 1.2) */}
        <Route path="/dashboard" element={<Dashboard />} />

        {/* Inspection Result — real screen (Step 1.4) */}
        <Route path="/inspections/:id" element={<InspectionResult />} />
        {/* New Inspection — real screen (Step 1.3) */}
        <Route path="/inspections/new" element={<NewInspection />} />
        {/* Inspection History — real screen (Step 1.5) */}
        <Route path="/inspections" element={<InspectionHistory />} />
        {/* AeroMemory — real screen (Step 1.6) */}
        <Route path="/aeromemory" element={<AeroMemory />} />
        {/* Reports — real screens (Step 1.7) */}
        <Route path="/reports" element={<Reports />} />
        <Route path="/reports/:id" element={<InspectionReport />} />
        {/* Model Performance — real screen (Step 1.8) */}
        <Route path="/model-performance" element={<ModelPerformance />} />
        {/* Settings — real screen (Step 1.9) */}
        <Route path="/settings" element={<Settings />} />

        {/* Mobile technician flow (real page exists; restyled in Step 1.10) */}
        <Route path="/mobile" element={<MobileCapturePage />} />

        {/* Catch-all redirects to landing */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
