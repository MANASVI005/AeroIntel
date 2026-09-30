import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Plane, 
  RotateCcw, 
  Camera, 
  Upload, 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  ShieldCheck,
  Activity,
  ArrowRight,
  Video,
  VideoOff,
  RefreshCw,
  Layers
} from 'lucide-react';

interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

interface DetectionItem {
  id: number;
  class_id: number;
  class_name: string;
  confidence: number;
  bbox: BoundingBox;
}

interface AeroMemoryComparison {
  defect_id: string;
  defect_type: string;
  state: string;
  severity: string;
  match_confidence: number;
}

interface AeroMemoryData {
  matched_count: number;
  new_count: number;
  comparisons: AeroMemoryComparison[];
}

interface InspectionResultResponse {
  inspection_id: number;
  inspection_code: string;
  inspection_image_id: number;
  original_filename: string;
  stored_path: string;
  image_width: number;
  image_height: number;
  detections: DetectionItem[];
  count: number;
  aeromemory?: AeroMemoryData;
}

export const DashboardPlaceholder: React.FC = () => {
  const navigate = useNavigate();

  // Mode: camera vs upload
  const [mode, setMode] = useState<'camera' | 'upload'>('camera');
  
  // Camera State
  const [isCameraActive, setIsCameraActive] = useState<boolean>(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);

  // Captured Image & Upload State
  const [capturedBlob, setCapturedBlob] = useState<Blob | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  // Inspection Payload Context
  const [inspectionsList, setInspectionsList] = useState<Array<{ id: number; inspection_code: string; panel_code?: string; aircraft_code?: string }>>([]);
  const [inspectionId, setInspectionId] = useState<string>('23');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [result, setResult] = useState<InspectionResultResponse | null>(null);

  // Dynamic API Base URL derived from browser hostname (supports laptop IP on LAN)
  const getApiBaseUrl = (): string => {
    const hostname = window.location.hostname || '127.0.0.1';
    return `http://${hostname}:8000`;
  };

  // Fetch active inspections list on dashboard mount
  useEffect(() => {
    const fetchInspections = async () => {
      try {
        const res = await fetch(`${getApiBaseUrl()}/api/inspections`);
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data) && data.length > 0) {
            setInspectionsList(data);
            setInspectionId(String(data[0].id));
          }
        }
      } catch (e) {
        console.warn('Could not fetch active inspections:', e);
      }
    };
    fetchInspections();
  }, []);

  // Stop camera tracks cleanly
  const stopCamera = () => {
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsCameraActive(false);
  };

  // Start local camera preview using navigator.mediaDevices.getUserMedia
  const startCamera = async () => {
    setCameraError(null);
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Browser camera API (getUserMedia) is not supported in this environment.');
      }
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });
      mediaStreamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setIsCameraActive(true);
    } catch (err: any) {
      console.error('Camera start error:', err);
      setCameraError(
        err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError'
          ? 'Camera access was denied. Please allow camera access or use local image upload.'
          : err.message || 'Camera is unavailable or in use by another application.'
      );
      setIsCameraActive(false);
    }
  };

  useEffect(() => {
    if (mode === 'camera') {
      startCamera();
    } else {
      stopCamera();
    }
    return () => {
      stopCamera();
    };
  }, [mode]);

  // Auto-polling effect to update dashboard when phone uploads an inspection photo
  useEffect(() => {
    const pollLatestResult = async () => {
      if (!inspectionId) return;
      try {
        const targetId = inspectionId.trim() || '23';
        const res = await fetch(`${getApiBaseUrl()}/api/inspections/${targetId}/latest-result`);
        if (res.ok) {
          const data = await res.json();
          if (data.has_result) {
            setResult(data);
          }
        }
      } catch (err) {
        // Silent polling catch
      }
    };

    pollLatestResult();
    const interval = setInterval(pollLatestResult, 2000);
    return () => clearInterval(interval);
  }, [inspectionId]);

  // Capture frame from canvas
  const handleCapture = () => {
    if (!videoRef.current) return;
    const video = videoRef.current;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 640;
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      canvas.toBlob((blob) => {
        if (blob) {
          setCapturedBlob(blob);
          const url = URL.createObjectURL(blob);
          setPreviewUrl(url);
        }
      }, 'image/jpeg', 0.95);
    }
  };

  // File upload handler
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setUploadFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  // Submit to local FastAPI server: POST /api/inspections/{inspection_id}/images
  const handleRunInspection = async () => {
    setApiError(null);
    setResult(null);

    let fileToUpload: File | null = null;
    if (mode === 'camera' && capturedBlob) {
      fileToUpload = new File([capturedBlob], `camera_capture_${Date.now()}.jpg`, { type: 'image/jpeg' });
    } else if (mode === 'upload' && uploadFile) {
      fileToUpload = uploadFile;
    }

    if (!fileToUpload) {
      setApiError('Please capture or select an inspection image first.');
      return;
    }

    setIsProcessing(true);
    try {
      const formData = new FormData();
      formData.append('file', fileToUpload);

      const targetInspId = inspectionId.trim() || '23';
      const response = await fetch(`${getApiBaseUrl()}/api/inspections/${targetInspId}/images`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.detail || `Inspection API returned status ${response.status}`);
      }

      const data: InspectionResultResponse = await response.json();
      setResult(data);
    } catch (err: any) {
      console.error('Inspection API submission failed:', err);
      setApiError(err.message || 'Inspection processing failed locally.');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#070e1b',
      color: '#f8fafc',
      display: 'flex',
      flexDirection: 'column',
      fontFamily: "'Inter', sans-serif"
    }}>
      {/* Top Navbar */}
      <header style={{
        height: '64px',
        borderBottom: '1px solid #1a283e',
        backgroundColor: '#091528',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 28px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '8px',
            backgroundColor: 'rgba(56, 189, 248, 0.12)',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#38bdf8'
          }}>
            <Plane size={20} />
          </div>
          <div>
            <span style={{
              fontWeight: 800,
              letterSpacing: '0.12em',
              fontSize: '1.05rem',
              color: '#ffffff'
            }}>
              AEROINTEL
            </span>
            <span style={{
              fontSize: '0.65rem',
              color: '#38bdf8',
              letterSpacing: '0.15em',
              marginLeft: '8px',
              padding: '2px 6px',
              borderRadius: '4px',
              backgroundColor: 'rgba(56, 189, 248, 0.1)'
            }}>
              LOCAL INSPECTION WORKSPACE
            </span>
          </div>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <button
            onClick={() => navigate('/')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '8px 16px',
              borderRadius: '6px',
              background: 'rgba(56, 189, 248, 0.1)',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              color: '#38bdf8',
              fontSize: '0.85rem',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
          >
            <RotateCcw size={15} />
            <span>Replay Intro</span>
          </button>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            paddingLeft: '16px',
            borderLeft: '1px solid #1a283e'
          }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              backgroundColor: '#0284c7',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 700,
              fontSize: '0.85rem'
            }}>
              BJ
            </div>
            <div style={{ fontSize: '0.82rem' }}>
              <div style={{ fontWeight: 600, color: '#f8fafc' }}>Bhakti Jagtap</div>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Aviation Engineer</div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main style={{ flex: 1, padding: '36px 40px', maxWidth: '1400px', margin: '0 auto', width: '100%' }}>
        
        {/* Header Title */}
        <div style={{ marginBottom: '28px' }}>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#ffffff', margin: '0 0 6px 0' }}>
            Aircraft Inspection Assistant
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.95rem', margin: 0 }}>
            Local camera capture &bull; Offline ONNX YOLO inference &bull; AeroMemory historical defect progression
          </p>
        </div>

        {/* Input Configuration & Mode Selection */}
        <div style={{
          backgroundColor: '#0b192e',
          border: '1px solid #1a2e4c',
          borderRadius: '12px',
          padding: '24px',
          marginBottom: '32px',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '20px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', color: '#94a3b8', marginBottom: '6px' }}>
                Inspection Target ID (DB)
              </label>
              <input
                type="text"
                value={inspectionId}
                onChange={(e) => setInspectionId(e.target.value)}
                style={{
                  backgroundColor: '#091528',
                  border: '1px solid #1e3a5f',
                  color: '#ffffff',
                  padding: '8px 14px',
                  borderRadius: '6px',
                  fontSize: '0.9rem',
                  width: '180px'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', color: '#94a3b8', marginBottom: '6px' }}>
                Inspection Mode
              </label>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  onClick={() => setMode('camera')}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '8px 16px',
                    borderRadius: '6px',
                    border: mode === 'camera' ? '1px solid #38bdf8' : '1px solid #1e3a5f',
                    backgroundColor: mode === 'camera' ? 'rgba(56, 189, 248, 0.15)' : '#091528',
                    color: mode === 'camera' ? '#38bdf8' : '#94a3b8',
                    fontWeight: 600,
                    fontSize: '0.85rem',
                    cursor: 'pointer'
                  }}
                >
                  <Camera size={16} />
                  <span>Live Camera</span>
                </button>

                <button
                  onClick={() => setMode('upload')}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '8px 16px',
                    borderRadius: '6px',
                    border: mode === 'upload' ? '1px solid #38bdf8' : '1px solid #1e3a5f',
                    backgroundColor: mode === 'upload' ? 'rgba(56, 189, 248, 0.15)' : '#091528',
                    color: mode === 'upload' ? '#38bdf8' : '#94a3b8',
                    fontWeight: 600,
                    fontSize: '0.85rem',
                    cursor: 'pointer'
                  }}
                >
                  <Upload size={16} />
                  <span>Upload Local File</span>
                </button>
              </div>
            </div>
          </div>

          <div>
            <button
              onClick={handleRunInspection}
              disabled={isProcessing}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '12px 28px',
                backgroundColor: isProcessing ? '#0284c7' : '#0284c7',
                opacity: isProcessing ? 0.7 : 1,
                color: '#ffffff',
                border: 'none',
                borderRadius: '8px',
                fontWeight: 700,
                fontSize: '0.95rem',
                cursor: isProcessing ? 'wait' : 'pointer',
                boxShadow: '0 4px 14px rgba(2, 132, 199, 0.35)'
              }}
            >
              {isProcessing ? <RefreshCw size={18} className="animate-spin" /> : <Activity size={18} />}
              <span>{isProcessing ? 'Processing ONNX & AeroMemory...' : 'RUN INSPECTION'}</span>
            </button>
          </div>
        </div>

        {/* Error Messages */}
        {cameraError && (
          <div style={{
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '8px',
            padding: '14px 20px',
            color: '#f87171',
            marginBottom: '24px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            fontSize: '0.9rem'
          }}>
            <AlertTriangle size={18} />
            <span>{cameraError}</span>
          </div>
        )}

        {apiError && (
          <div style={{
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '8px',
            padding: '14px 20px',
            color: '#f87171',
            marginBottom: '24px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            fontSize: '0.9rem'
          }}>
            <AlertTriangle size={18} />
            <span>{apiError}</span>
          </div>
        )}

        {/* Capture Workspace Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: mode === 'camera' ? '1fr 1fr' : '1fr',
          gap: '24px',
          marginBottom: '36px'
        }}>
          {/* Live Camera View */}
          {mode === 'camera' && (
            <div style={{
              backgroundColor: '#091528',
              border: '1px solid #1a283e',
              borderRadius: '12px',
              padding: '20px',
              display: 'flex',
              flexDirection: 'column'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                <span style={{ fontWeight: 700, fontSize: '0.95rem', color: '#ffffff', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Video size={18} color="#38bdf8" />
                  Live Camera Preview
                </span>
                <span style={{ fontSize: '0.75rem', color: isCameraActive ? '#10b981' : '#f87171' }}>
                  {isCameraActive ? '● CAMERA ACTIVE' : '○ DISCONNECTED'}
                </span>
              </div>

              <div style={{
                position: 'relative',
                width: '100%',
                height: '340px',
                backgroundColor: '#030712',
                borderRadius: '8px',
                overflow: 'hidden',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '1px solid #1e293b'
              }}>
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  style={{
                    width: '100%',
                    height: '100%',
                    objectFit: 'cover',
                    display: isCameraActive ? 'block' : 'none'
                  }}
                />

                {!isCameraActive && (
                  <div style={{ textAlign: 'center', color: '#64748b' }}>
                    <VideoOff size={36} style={{ marginBottom: '8px' }} />
                    <p style={{ margin: 0, fontSize: '0.85rem' }}>Camera feed unavailable</p>
                  </div>
                )}
              </div>

              <button
                onClick={handleCapture}
                disabled={!isCameraActive}
                style={{
                  marginTop: '16px',
                  padding: '12px',
                  backgroundColor: isCameraActive ? '#0284c7' : '#334155',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '6px',
                  fontWeight: 700,
                  fontSize: '0.9rem',
                  cursor: isCameraActive ? 'pointer' : 'not-allowed',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px'
                }}
              >
                <Camera size={18} />
                <span>CAPTURE IMAGE</span>
              </button>
            </div>
          )}

          {/* Captured Image / Uploaded Preview Panel */}
          <div style={{
            backgroundColor: '#091528',
            border: '1px solid #1a283e',
            borderRadius: '12px',
            padding: '20px',
            display: 'flex',
            flexDirection: 'column'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <span style={{ fontWeight: 700, fontSize: '0.95rem', color: '#ffffff', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Layers size={18} color="#38bdf8" />
                {mode === 'camera' ? 'Captured Image Preview' : 'Local Image Upload'}
              </span>
            </div>

            {mode === 'upload' ? (
              <div style={{ marginBottom: '16px' }}>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleFileChange}
                  style={{
                    width: '100%',
                    padding: '12px',
                    backgroundColor: '#030712',
                    border: '1px dashed #1e3a5f',
                    borderRadius: '8px',
                    color: '#94a3b8'
                  }}
                />
              </div>
            ) : null}

            <div style={{
              position: 'relative',
              width: '100%',
              height: '340px',
              backgroundColor: '#030712',
              borderRadius: '8px',
              overflow: 'hidden',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: '1px solid #1e293b'
            }}>
              {previewUrl ? (
                <img
                  src={previewUrl}
                  alt="Captured Inspection Frame"
                  style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                />
              ) : (
                <div style={{ textAlign: 'center', color: '#64748b' }}>
                  <Camera size={36} style={{ marginBottom: '8px' }} />
                  <p style={{ margin: 0, fontSize: '0.85rem' }}>No frame captured yet</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Results Panel */}
        {result && (
          <div style={{
            backgroundColor: '#091528',
            border: '1px solid #1e3a5f',
            borderRadius: '12px',
            padding: '28px',
            marginBottom: '32px'
          }}>
            <h2 style={{ fontSize: '1.3rem', fontWeight: 800, color: '#ffffff', margin: '0 0 20px 0', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <CheckCircle2 color="#10b981" size={24} />
              Inspection Results & AeroMemory Intelligence
            </h2>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '24px',
              marginBottom: '28px'
            }}>
              {/* Detections Card */}
              <div style={{ backgroundColor: '#0b192e', padding: '20px', borderRadius: '10px', border: '1px solid #1a2e4c' }}>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#38bdf8', marginTop: 0, marginBottom: '14px' }}>
                  ONNX YOLO Detections ({result.count})
                </h3>
                {result.detections.length === 0 ? (
                  <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>No surface defects detected on this panel.</p>
                ) : (
                  result.detections.map((det) => (
                    <div key={det.id} style={{
                      backgroundColor: '#091528',
                      padding: '12px',
                      borderRadius: '6px',
                      marginBottom: '10px',
                      borderLeft: '4px solid #f59e0b'
                    }}>
                      <div style={{ fontWeight: 700, color: '#ffffff', fontSize: '0.9rem' }}>
                        Class: {det.class_name}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '4px' }}>
                        Confidence: {(det.confidence * 100).toFixed(1)}%
                      </div>
                      <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '2px', fontFamily: "'JetBrains Mono', monospace" }}>
                        BBox: [{det.bbox.x.toFixed(1)}, {det.bbox.y.toFixed(1)}, {det.bbox.width.toFixed(1)}, {det.bbox.height.toFixed(1)}]
                      </div>
                    </div>
                  ))
                )}
              </div>

              {/* AeroMemory Card */}
              <div style={{ backgroundColor: '#0b192e', padding: '20px', borderRadius: '10px', border: '1px solid #1a2e4c' }}>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#38bdf8', marginTop: 0, marginBottom: '14px' }}>
                  AeroMemory Defect Tracking
                </h3>
                {result.aeromemory ? (
                  <div>
                    <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '12px' }}>
                      Matched Existing Defects: <strong style={{ color: '#ffffff' }}>{result.aeromemory.matched_count}</strong> &bull; New Defects: <strong style={{ color: '#ffffff' }}>{result.aeromemory.new_count}</strong>
                    </div>

                    {result.aeromemory.comparisons.map((comp, idx) => (
                      <div key={idx} style={{
                        backgroundColor: '#091528',
                        padding: '12px',
                        borderRadius: '6px',
                        marginBottom: '10px',
                        borderLeft: '4px solid #38bdf8'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontWeight: 700, color: '#ffffff', fontSize: '0.9rem' }}>
                            Defect Code: {comp.defect_id}
                          </span>
                          <span style={{
                            fontSize: '0.72rem',
                            padding: '2px 8px',
                            borderRadius: '4px',
                            backgroundColor: comp.state === 'Progressing' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                            color: comp.state === 'Progressing' ? '#f87171' : '#34d399',
                            fontWeight: 700
                          }}>
                            {comp.state}
                          </span>
                        </div>
                        <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '6px' }}>
                          Type: {comp.defect_type} &bull; Severity: {comp.severity} &bull; Match Score: {(comp.match_confidence * 100).toFixed(1)}%
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>No AeroMemory history available for this upload.</p>
                )}
              </div>
            </div>

            <div style={{ fontSize: '0.78rem', color: '#64748b', borderTop: '1px solid #1a2e4c', paddingTop: '14px' }}>
              Stored local image: <code style={{ color: '#38bdf8' }}>{result.stored_path}</code>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default DashboardPlaceholder;
