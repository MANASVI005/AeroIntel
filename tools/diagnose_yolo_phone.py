import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path("backend").resolve()))

import cv2
from sqlalchemy import text
from app.db.database import engine
from app.services.model_service import AeroIntelModel

def main():
    print("=== TASK 1: IDENTIFY UPLOADED PHONE IMAGE ===")
    with engine.connect() as conn:
        res = conn.execute(text(
            "SELECT ii.id as img_id, ii.inspection_id, i.inspection_code, ii.image_path, "
            "ii.original_filename, ii.image_width, ii.image_height "
            "FROM inspection_image ii "
            "JOIN inspection i ON ii.inspection_id = i.id "
            "ORDER BY ii.id DESC LIMIT 1;"
        )).first()
        
    if not res:
        print("No inspection images found in database!")
        return
        
    phone_img_info = dict(res._mapping)
    print(f"Inspection ID: {phone_img_info['inspection_id']}")
    print(f"Inspection Code: {phone_img_info['inspection_code']}")
    print(f"Image ID: {phone_img_info['img_id']}")
    print(f"Exact Stored Image Path: {phone_img_info['image_path']}")
    
    img_path = Path(phone_img_info['image_path'])
    if not img_path.exists():
        print(f"ERROR: Image file does not exist at {img_path}")
        return
        
    file_size_bytes = img_path.stat().st_size
    print(f"File Size: {file_size_bytes} bytes ({file_size_bytes / 1024 / 1024:.2f} MB)")
    
    cv_img = cv2.imread(str(img_path))
    if cv_img is None:
        print("OpenCV Read Status: FAILED (cv2.imread returned None)")
        return
    else:
        h, w, c = cv_img.shape
        print(f"OpenCV Read Status: SUCCESS")
        print(f"Image Width: {w}, Height: {h}, Channels: {c}")

    print("\n=== TASK 4: VERIFY ONNX MODEL ===")
    model_path = Path("models/aerointel_v1.onnx")
    print(f"Exact Model Path: {model_path.resolve()}")
    print(f"Model File Size: {model_path.stat().st_size} bytes ({model_path.stat().st_size / 1024 / 1024:.2f} MB)")
    print(f"Model Modified Time: {model_path.stat().st_mtime}")
    
    model_service = AeroIntelModel(model_path=model_path, confidence=0.40, iou=0.50, image_size=640)
    print("Model Loaded Successfully!")
    
    print("\n=== TASK 2: RUN PRODUCTION MODEL SERVICE ON PHONE IMAGE ===")
    print(f"Image: {img_path}")
    print(f"Model: {model_path}")
    print(f"Image Dimensions: {w}x{h}")
    print(f"Inference Settings: conf={model_service.confidence}, iou={model_service.iou}, imgsz={model_service.image_size}")
    
    # Run ultralytics predict directly to see raw vs final
    raw_results = model_service.model.predict(
        str(img_path),
        imgsz=model_service.image_size,
        conf=0.01, # lower threshold to see if ANY raw detection exists
        iou=model_service.iou,
        verbose=False
    )
    raw_boxes = raw_results[0].boxes
    print(f"\nRaw Detections at conf >= 0.01: {len(raw_boxes) if raw_boxes is not None else 0}")
    if raw_boxes is not None and len(raw_boxes) > 0:
        for box in raw_boxes:
            c_id = int(box.cls.item())
            c_name = model_service.model.names.get(c_id, f"Unknown ({c_id})")
            c_conf = float(box.conf.item())
            b_xyxy = [float(v) for v in box.xyxy[0].tolist()]
            print(f"  - Raw Detection: Class ID={c_id} ({c_name}), Conf={c_conf:.4f}, BBox={b_xyxy}")

    phone_detections = model_service.detect(img_path)
    print(f"\nFinal Detections at conf >= {model_service.confidence}: {len(phone_detections)}")
    for det in phone_detections:
        print(f"  - Class ID={det['class_id']} ({det['class_name']}), Conf={det['confidence']:.4f}, BBox={det['bbox']}")

    print("\n=== TASK 3: COMPARE AGAINST KNOWN-GOOD LOCAL DEFECT IMAGE ===")
    # Find a known-good image in DB with detections
    with engine.connect() as conn:
        known_good_res = conn.execute(text(
            "SELECT ii.id as img_id, ii.image_path, count(d.id) as det_count "
            "FROM inspection_image ii "
            "JOIN detection d ON d.inspection_image_id = ii.id "
            "GROUP BY ii.id, ii.image_path "
            "ORDER BY ii.id DESC LIMIT 1;"
        )).first()
        
    if known_good_res:
        kg_path = Path(known_good_res._mapping['image_path'])
        print(f"Known-Good Image Path: {kg_path}")
        kg_cv_img = cv2.imread(str(kg_path))
        kg_h, kg_w, _ = kg_cv_img.shape
        kg_detections = model_service.detect(kg_path)
        
        print("\n--- SIDE BY SIDE COMPARISON ---")
        print(f"Known-good image:")
        print(f"  dimensions: {kg_w}x{kg_h}")
        print(f"  detections: {len(kg_detections)}")
        print(f"  classes: {[d['class_name'] for d in kg_detections]}")
        print(f"  confidences: {[round(d['confidence'], 4) for d in kg_detections]}")
        print(f"\nPhone image:")
        print(f"  dimensions: {w}x{h}")
        print(f"  detections: {len(phone_detections)}")
        print(f"  classes: {[d['class_name'] for d in phone_detections]}")
        print(f"  confidences: {[round(d['confidence'], 4) for d in phone_detections]}")

if __name__ == '__main__':
    main()
