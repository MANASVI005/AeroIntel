import React, { useState, useEffect, useRef } from 'react';
import { Plane, Camera, Send, CheckCircle2, AlertTriangle, RefreshCw, RefreshCw as RetakeIcon } from 'lucide-react';

interface InspectionOption {
  id: number;
  inspection_code: string;
  panel_code: string | null;
  aircraft_code: string | null;
}

export const MobileCapturePage: React.FC = () => {
  const [inspections, setInspections] = useState<InspectionOption[]>([]);
  const [selectedInspectionId, setSelectedInspectionId] = useState<string>('23');
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [capturedFile, setCapturedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState<boolean>(false);

  // Dynamic API Base URL derived from current hostname (supports LAN IP automatically)
  const getApiBaseUrl = (): string => {
    const hostname = window.location.hostname || '127.0.0.1';
    return `http://${hostname}:8000`;
  };

  // Fetch available inspections from local backend
  useEffect(() => {
    const fetchInspections = async () => {
      try {
        const res = await fetch(`${getApiBaseUrl()}/api/inspections`);
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data) && data.length > 0) {
            setInspections(data);
            setSelectedInspectionId((prev) => prev || String(data[0].id));
          }
        }
      } catch (e) {
        console.warn('Could not fetch inspection list:', e);
      }
    };
    fetchInspections();
  }, []);

  // Handle file input change (Native mobile camera capture)
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setCapturedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setStatusMessage(null);
      setIsSuccess(false);
    }
  };

  // Trigger hidden native file input
  const triggerNativeCamera = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  // Retake photo
  const handleRetake = () => {
    setCapturedFile(null);
    setPreviewUrl(null);
    setStatusMessage(null);
    setIsSuccess(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Upload photo to existing backend endpoint: POST /api/inspections/{inspection_id}/images
  const handleUploadAndInspect = async () => {
    if (!capturedFile) {
      setStatusMessage('Please capture or select a photo first.');
      setIsSuccess(false);
      return;
    }

    setIsUploading(true);
    setStatusMessage('Sending photo to AeroIntel Edge Laptop...');
    setIsSuccess(false);

    try {
      const formData = new FormData();
      formData.append('file', capturedFile);

      const targetId = selectedInspectionId || '23';
      const response = await fetch(`${getApiBaseUrl()}/api/inspections/${targetId}/images`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || `Upload failed (Status ${response.status})`);
      }

      const data = await response.json();
      setIsSuccess(true);
      setStatusMessage(`Inspection processed on laptop! (${data.count} detections, ${data.aeromemory?.matched_count || 0} matched defects)`);
    } catch (err: any) {
      console.error('Mobile upload error:', err);
      setIsSuccess(false);
      setStatusMessage(err.message || 'Failed to upload photo to laptop.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#070e1b',
      color: '#f8fafc',
      padding: '16px',
      display: 'flex',
      flexDirection: 'column',
      fontFamily: "'Inter', sans-serif"
    }}>
      {/* Hidden native HTML camera input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        onChange={handleFileChange}
        style={{ position: 'absolute', top: '-9999px', left: '-9999px', opacity: 0, width: '1px', height: '1px' }}
      />

      {/* Header */}
      <header style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingBottom: '14px',
        borderBottom: '1px solid #1a283e',
        marginBottom: '16px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: '6px',
            backgroundColor: 'rgba(56, 189, 248, 0.15)',
            border: '1px solid rgba(56, 189, 248, 0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#38bdf8'
          }}>
            <Plane size={18} />
          </div>
          <div>
            <div style={{ fontWeight: 800, fontSize: '0.95rem', color: '#ffffff', letterSpacing: '0.05em' }}>
              AEROINTEL MOBILE
            </div>
            <div style={{ fontSize: '0.7rem', color: '#38bdf8' }}>
              Technician Camera Client
            </div>
          </div>
        </div>

        <span style={{ fontSize: '0.7rem', color: '#10b981', fontWeight: 700 }}>
          ● NATIVE CAM READY
        </span>
      </header>

      {/* Target Inspection Selection */}
      <div style={{ marginBottom: '16px' }}>
        <label style={{ display: 'block', fontSize: '0.78rem', color: '#94a3b8', marginBottom: '6px' }}>
          Select Active Inspection Target:
        </label>
        {inspections.length > 0 ? (
          <select
            value={selectedInspectionId}
            onChange={(e) => setSelectedInspectionId(e.target.value)}
            style={{
              width: '100%',
              backgroundColor: '#091528',
              border: '1px solid #1e3a5f',
              color: '#ffffff',
              padding: '10px 14px',
              borderRadius: '8px',
              fontSize: '0.88rem'
            }}
          >
            {inspections.map((insp) => (
              <option key={insp.id} value={insp.id}>
                Inspection #{insp.id} ({insp.inspection_code}) - {insp.aircraft_code || 'Aircraft'} / {insp.panel_code || 'Panel'}
              </option>
            ))}
          </select>
        ) : (
          <input
            type="text"
            value={selectedInspectionId}
            onChange={(e) => setSelectedInspectionId(e.target.value)}
            placeholder="Inspection ID (e.g. 23)"
            style={{
              width: '100%',
              backgroundColor: '#091528',
              border: '1px solid #1e3a5f',
              color: '#ffffff',
              padding: '10px 14px',
              borderRadius: '8px',
              fontSize: '0.88rem'
            }}
          />
        )}
      </div>

      {/* Camera Preview / Snapshot */}
      <div style={{
        position: 'relative',
        width: '100%',
        height: '280px',
        backgroundColor: '#030712',
        borderRadius: '12px',
        overflow: 'hidden',
        border: '1px solid #1e293b',
        marginBottom: '16px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        {previewUrl ? (
          <img src={previewUrl} alt="Captured Photo" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
        ) : (
          <div style={{ textAlign: 'center', color: '#64748b', padding: '20px' }}>
            <Camera size={48} color="#38bdf8" style={{ marginBottom: '12px' }} />
            <div style={{ fontSize: '0.9rem', color: '#f8fafc', fontWeight: 600, marginBottom: '4px' }}>
              No Inspection Photo Captured
            </div>
            <div style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
              Tap 'Capture Image' below to open rear phone camera
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div style={{ display: 'grid', gridTemplateColumns: previewUrl ? '1fr 1fr' : '1fr', gap: '12px', marginBottom: '16px' }}>
        {previewUrl ? (
          <button
            onClick={handleRetake}
            style={{
              padding: '14px',
              backgroundColor: '#1e293b',
              color: '#94a3b8',
              border: '1px solid #334155',
              borderRadius: '8px',
              fontWeight: 700,
              fontSize: '0.92rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              cursor: 'pointer'
            }}
          >
            <RetakeIcon size={18} />
            <span>RETAKE PHOTO</span>
          </button>
        ) : (
          <button
            onClick={triggerNativeCamera}
            style={{
              padding: '14px',
              backgroundColor: '#0284c7',
              color: '#ffffff',
              border: 'none',
              borderRadius: '8px',
              fontWeight: 700,
              fontSize: '0.95rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              cursor: 'pointer',
              boxShadow: '0 4px 14px rgba(2, 132, 199, 0.35)'
            }}
          >
            <Camera size={20} />
            <span>CAPTURE IMAGE</span>
          </button>
        )}

        {previewUrl && (
          <button
            onClick={handleUploadAndInspect}
            disabled={isUploading}
            style={{
              padding: '14px',
              backgroundColor: '#10b981',
              opacity: isUploading ? 0.7 : 1,
              color: '#ffffff',
              border: 'none',
              borderRadius: '8px',
              fontWeight: 700,
              fontSize: '0.92rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              cursor: isUploading ? 'wait' : 'pointer',
              boxShadow: '0 4px 14px rgba(16, 185, 129, 0.35)'
            }}
          >
            {isUploading ? <RefreshCw size={18} className="animate-spin" /> : <Send size={18} />}
            <span>{isUploading ? 'SENDING...' : 'UPLOAD & INSPECT'}</span>
          </button>
        )}
      </div>

      {/* Status Alert Banner */}
      {statusMessage && (
        <div style={{
          backgroundColor: isSuccess ? 'rgba(16, 185, 129, 0.12)' : 'rgba(2, 132, 199, 0.15)',
          border: isSuccess ? '1px solid rgba(16, 185, 129, 0.4)' : '1px solid rgba(56, 189, 248, 0.3)',
          borderRadius: '8px',
          padding: '14px',
          color: isSuccess ? '#34d399' : '#38bdf8',
          fontSize: '0.85rem',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          {isSuccess ? <CheckCircle2 size={18} /> : <RefreshCw size={18} />}
          <span>{statusMessage}</span>
        </div>
      )}

      {/* Footer Info */}
      <footer style={{ marginTop: 'auto', paddingTop: '16px', textAlign: 'center', fontSize: '0.72rem', color: '#64748b' }}>
        AeroIntel Local Wi-Fi Client &bull; Connects to <code style={{ color: '#38bdf8' }}>{getApiBaseUrl()}</code>
      </footer>
    </div>
  );
};

export default MobileCapturePage;
