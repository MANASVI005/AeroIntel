# AeroIntel Real-Time Mobile Image Capture & Inference Guide

This document details the real-time mobile camera capture architecture, LAN connection workflow, image resolution downscaling analysis, framing guidelines, and tiling preprocessor specifications for AeroIntel.

---

## 📱 1. Air-Gapped Two-Device LAN Workflow

AeroIntel operates completely air-gapped in aircraft hangars over a local Wi-Fi router or laptop mobile hotspot without internet connectivity.

```text
📱 TECHNICIAN PHONE                                 💻 AEROINTEL EDGE LAPTOP
┌────────────────────────────────┐                 ┌────────────────────────────────┐
│ http://<LAPTOP_IP>:3000/mobile │                 │ http://localhost:3000          │
│                                │                 │ (React Inspection Dashboard)   │
│ 1. Select Target Inspection ID │                 └───────────────┬────────────────┘
│ 2. Tap 'CAPTURE IMAGE'         │                                 │
│ 3. Native Rear Camera opens    │                                 │ Polls every 2s for
│ 4. Take Photo & Confirm        │                                 │ latest result
│ 5. Tap 'UPLOAD & INSPECT'      │                                 │
└───────────────┬────────────────┘                                 │
                │                                                  │
                │ POST /api/inspections/{id}/images                │
                └────────────────────────┐                         │
                                         ▼                         ▼
                               ┌──────────────────────────────────────────┐
                               │           FastAPI Laptop Server          │
                               │                (Port 8000)               │
                               └────────────────────┬─────────────────────┘
                                                    │
                                                    ▼
                               ┌──────────────────────────────────────────┐
                               │ 1. Save Image to Local Laptop Disk       │
                               │ 2. Execute YOLO ONNX Inference           │
                               │ 3. Run AeroMemory Spatiotemporal Match   │
                               │ 4. Persist to Local PostgreSQL DB        │
                               └──────────────────────────────────────────┘
```

---

## 📷 2. Mobile HTML5 Camera Bridge Specification

To ensure compatibility across mobile web browsers on plain HTTP local LAN IP addresses (where `navigator.mediaDevices.getUserMedia()` is blocked by WebKit/Chrome security policies), AeroIntel uses native HTML5 file inputs:

```tsx
<input
  ref={fileInputRef}
  type="file"
  accept="image/*"
  capture="environment"
  onChange={handleFileChange}
  style={{ position: 'absolute', top: '-9999px', left: '-9999px', opacity: 0, width: '1px', height: '1px' }}
/>
```

### Key Technical Attributes
- **`capture="environment"`**: Directly invokes the smartphone's native rear camera app when triggered.
- **Off-screen Absolute Positioning (`top: -9999px`)**: Keeps the element attached to the visible rendering tree so browser OS file selector bridges do not drop the selection state when returning from the native camera activity.
- **`URL.createObjectURL(file)`**: Generates an immediate local blob preview on the phone UI prior to transmission.
- **Multipart Form Data Transfer**: Sends raw original `File` bytes directly to `POST /api/inspections/{inspection_id}/images`.

---

## 🔍 3. Resolution Downscaling & Detection Analysis

When testing real-time phone camera capture, you may notice that a wide photo of an aircraft section returns `ONNX YOLO Detections (0)`. The diagnostic investigation revealed the exact underlying cause:

### The 4K Downscaling Phenomenon
1. **Camera Native Resolution**: Modern smartphones capture photos at **3072 × 4096 resolution** (12 Megapixels).
2. **YOLO Input Layer**: The production model `aerointel_v1.onnx` receives input scaled to **640 × 640 resolution**.
3. **Resolution Loss**: Shrinking a 3072×4096 photo down to 640×640 compresses image dimensions by **6.4×**. A small physical defect (e.g., a fine 30×30 pixel crack on the phone photo) shrinks to under **5×5 pixels** in YOLO input space.
4. **Feature Map Suppression**: Extremely small feature maps result in detection confidence falling below the model's `conf = 0.40` threshold, producing 0 detections.

---

## 🎯 4. Field Framing Best Practices for Technicians

To achieve instant, high-confidence bounding box detections on the laptop dashboard using the current production model:

1. **Close-Up Framing (Macro Shot)**:
   Position the phone camera **10 cm to 30 cm** from the target defect, filling 30% to 70% of the frame with the affected aircraft surface.
2. **Perpendicular Angle**:
   Hold the phone directly facing the panel surface to minimize perspective distortion.
3. **Adequate Surface Lighting**:
   Ensure hangar lighting or a flashlight illuminates the panel to bring out crack edges and corrosion discoloration.

---

## 🧩 5. Future Tiling / Sliding-Window Preprocessor Specification

To support wide-angle, full-panel 4K phone photos in future iterations without retraining the YOLO model, a sliding-window tiler can be enabled in `backend/app/services/model_service.py`:

```text
       HIGH-RES 4K PHONE PHOTO (3072 x 4096)
┌─────────────────────────────────────────────────┐
│  Tile 1 [640x640]  │  Tile 2 [640x640]  │ ...   │
│  Native 1:1 pixels │  Native 1:1 pixels │       │
├────────────────────┼────────────────────┼───────┤
│  Tile 4 [640x640]  │  Tile 5 (DEFECT)   │ ...   │
│  Native 1:1 pixels │  Native 1:1 pixels │       │
└────────────────────┴────────────────────┴───────┘
```

### Algorithm Steps:
1. Divide high-res `3072x4096` image into overlapping `640x640` tiles (e.g. 20% stride overlap).
2. Run YOLO ONNX inference on each un-scaled `640x640` tile.
3. Translate tile-local box coordinates back to global image coordinates:
   $$X_{global} = X_{tile\_offset} + X_{local}$$
   $$Y_{global} = Y_{tile\_offset} + Y_{local}$$
4. Apply Non-Maximum Suppression (NMS) across the global image to merge boundary-overlapping detections.
