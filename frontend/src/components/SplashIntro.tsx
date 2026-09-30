import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface SplashIntroProps {
  onComplete?: () => void;
  targetRoute?: string;
}

export const SplashIntro: React.FC<SplashIntroProps> = ({
  onComplete,
  targetRoute = '/dashboard',
}) => {
  const navigate = useNavigate();
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isFading, setIsFading] = useState<boolean>(false);

  const goToDashboard = () => {
    if (onComplete) {
      onComplete();
    } else {
      navigate(targetRoute, { replace: true });
    }
  };

  useEffect(() => {
    // Start video playback
    if (videoRef.current) {
      videoRef.current.playbackRate = 1.0;
      videoRef.current.play().catch((err) => {
        console.warn('Video autoplay was deferred by browser:', err);
      });
    }

    // At 4s: begin 1-second fade-out
    const fadeTimer = setTimeout(() => {
      setIsFading(true);
    }, 4000);

    // At 5s: navigate to dashboard
    const navigateTimer = setTimeout(() => {
      goToDashboard();
    }, 5000);

    // ESC key skips intro
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') goToDashboard();
    };
    window.addEventListener('keydown', handleKeyDown);

    return () => {
      clearTimeout(fadeTimer);
      clearTimeout(navigateTimer);
      window.removeEventListener('keydown', handleKeyDown);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div
      className={`splash-root${isFading ? ' splash-fading' : ''}`}
      role="banner"
      aria-label="AeroIntel — Loading"
    >
      {/* ── Deep navy radial background ── */}
      <div className="splash-bg" />

      {/* ── Subtle aviation grid overlay ── */}
      <div className="splash-grid" />

      {/* ── Top status bar ── */}
      <div className="splash-status-bar">
        <div className="splash-status-left">
          <span className="splash-status-dot" />
          <span>AEROINTEL SYSTEM READY</span>
        </div>
        <button
          className="splash-skip-btn"
          onClick={goToDashboard}
          type="button"
          aria-label="Skip intro"
        >
          SKIP &nbsp;[ESC]
        </button>
      </div>

      {/* ── Central layout: branding above, aircraft below ── */}
      <div className="splash-center">

        {/* Branding block */}
        <div className="splash-branding">
          <h1 className="splash-logo">AEROINTEL</h1>
          <div className="splash-badge">
            <span className="splash-badge-dot" />
            <span className="splash-badge-text">AI-POWERED AIRCRAFT INSPECTION</span>
          </div>
          <p className="splash-tagline">&ldquo;Smarter Inspections. Safer Skies.&rdquo;</p>
        </div>

        {/* Aircraft video — large, centered, semi-transparent */}
        <div className="splash-aircraft-wrap">
          <video
            ref={videoRef}
            className="splash-aircraft-video"
            src="/videos/aircraft.mp4"
            autoPlay
            muted
            loop
            playsInline
            aria-hidden="true"
          />
          {/* Soft glow behind the aircraft */}
          <div className="splash-aircraft-glow" />
        </div>

      </div>

      {/* ── 5-second linear progress bar along the bottom ── */}
      <div className="splash-progress-track">
        <div className="splash-progress-fill" />
      </div>
    </div>
  );
};
