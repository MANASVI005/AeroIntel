import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { useHealth } from '../../hooks/useHealth';
import { imageBaseUrl } from '../../services/api';

/**
 * AppShell — left sidebar + top bar + content area.
 * Markup traced verbatim from stitch/aerointel_inspection_result.html.
 * NO-HOLLOW-UI pass (Step 1.9): the fake "Last sync: just now • Edge Node
 * Active" chip, decorative notifications bell and invented "A. Sharma" user
 * identity are gone. Status chips are now REAL:
 *   - Backend live/offline ← GET /health (30 s polling via useHealth)
 *   - API location ← the actual configured base URL (VITE_API_URL or default)
 * The decorative topbar search was removed too — there is no search backend.
 */

const NAV_ITEMS = [
  { to: '/dashboard', icon: 'space_dashboard', label: 'Dashboard' },
  { to: '/inspections/new', icon: 'add_circle', label: 'New Inspection' },
  { to: '/inspections', icon: 'history', label: 'Inspection History' },
  { to: '/aeromemory', icon: 'neurology', label: 'AeroMemory' },
  { to: '/reports', icon: 'summarize', label: 'Reports' },
  { to: '/model-performance', icon: 'query_stats', label: 'Model Performance' },
  { to: '/settings', icon: 'settings', label: 'Settings' },
];

const apiHost = (() => {
  try {
    return new URL(imageBaseUrl).host;
  } catch {
    return imageBaseUrl;
  }
})();

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const { online, dbConnected } = useHealth();
  const [lastSync, setLastSync] = useState<Date | null>(null);

  // Track when the last successful /health poll happened → real "last sync".
  useEffect(() => {
    if (online) setLastSync(new Date());
  }, [online]);

  return (
    <>
      {/* ── Sidebar ── */}
      <aside className="fixed left-0 top-0 h-full w-72 bg-surface-container-lowest/90 backdrop-blur-xl shadow-[0_1px_8px_rgba(0,0,0,0.04)] z-50 flex flex-col justify-between py-6 px-4">
        <div className="flex flex-col gap-6">
          <div className="flex items-center gap-3 px-3">
            <a href="/" aria-label="AeroIntel — go to landing page" className="flex items-center">
              <img
                src="/brand/aerointel-logo.png"
                alt="AeroIntel"
                className="h-9 w-auto object-contain"
              />
            </a>
            <div className="flex flex-col">
              <span className="font-caption-data text-caption-data text-on-surface-variant">
                Smart Inspection. Safer Skies.
              </span>
            </div>
          </div>

          <nav className="flex flex-col gap-1">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  isActive
                    ? 'flex items-center gap-3 px-3 py-2.5 rounded-xl font-body-md text-body-md bg-primary-container text-on-primary-container font-semibold rounded-xl shadow-[0_10px_24px_rgba(160,195,225,0.20)] transition-all'
                    : 'flex items-center gap-3 px-3 py-2.5 rounded-xl font-body-md text-body-md text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-all'
                }
              >
                <span className="material-symbols-outlined text-[20px]">{item.icon}</span>
                <span>{item.label}</span>
              </NavLink>
            ))}
          </nav>
        </div>

        <div className="flex flex-col gap-3 px-3 pt-4">
          <div className="flex items-center justify-between bg-surface-container-low/80 px-3 py-2 rounded-xl">
            <div className="flex items-center gap-2">
              <span
                className={`w-2 h-2 rounded-full ${online ? 'bg-tertiary-container animate-pulse' : 'bg-error'}`}
              />
              <span
                className={`font-caption-data text-caption-data font-semibold ${online ? 'text-tertiary' : 'text-error'}`}
              >
                {online ? 'Backend Online' : 'Backend Offline'}
              </span>
            </div>
            <span className="font-caption-data text-caption-data px-2 py-0.5 rounded-full bg-secondary-fixed text-on-secondary-fixed-variant">
              v1.0.0
            </span>
          </div>
        </div>
      </aside>

      {/* ── Content column ── */}
      <div className="pl-72">
        {/* Top bar */}
        <header className="fixed top-0 left-72 right-0 h-16 bg-surface-container-lowest/80 backdrop-blur-xl shadow-[0_1px_8px_rgba(0,0,0,0.04)] z-40 flex items-center justify-between px-8">
          {/* Real live status ← GET /health */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface-container text-on-surface font-caption-data text-caption-data">
            <span className={`w-1.5 h-1.5 rounded-full ${online ? 'bg-primary' : 'bg-error'}`} />
            <span>
              {online
                ? `Live · checked ${lastSync ? lastSync.toLocaleTimeString() : 'just now'}`
                : 'Backend offline'}
            </span>
          </div>
          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface-container text-on-surface font-caption-data text-caption-data">
              <span className="material-symbols-outlined text-[16px]">dns</span>
              <span>API {apiHost}</span>
              {dbConnected && <span className="w-1.5 h-1.5 rounded-full bg-tertiary" aria-label="database connected" />}
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="relative pt-16 bg-background min-h-screen w-full px-8 py-6">
          <div className="flex flex-col w-full gap-6 pb-12">{children}</div>
        </main>
      </div>
    </>
  );
};

export default AppShell;
