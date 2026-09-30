from pathlib import Path

from ultralytics import YOLO


MODEL_PATH = Path("models/aerointel_v1.onnx")

CLASS_NAMES = {
    0: "Crack",
    1: "Corrosion",
    2: "Dent",
    3: "Missing Fastener",
}


class AeroIntelModel:
    def __init__(
        self,
        model_path: Path = MODEL_PATH,
        confidence: float = 0.40,
        iou: float = 0.50,
        image_size: int = 640,
    ):
        if not model_path.exists():
            raise FileNotFoundError(
                f"AeroIntel model not found: {model_path}"
            )

        print(f"Loading AeroIntel model: {model_path}")

        self.model = YOLO(str(model_path))
        self.confidence = confidence
        self.iou = iou
        self.image_size = image_size

    def detect(self, image_path: str | Path) -> list[dict]:
        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(
                f"Image not found: {image_path}"
            )

        results = self.model.predict(
            str(image_path),
            imgsz=self.image_size,
            conf=self.confidence,
            iou=self.iou,
            verbose=False,
        )

        result = results[0]
        detections = []

        if result.boxes is None:
            return detections

        for box in result.boxes:
            class_id = int(box.cls.item())
            confidence = float(box.conf.item())

            x1, y1, x2, y2 = (
                float(value)
                for value in box.xyxy[0].tolist()
            )

            detections.append(
                {
                    "class_id": class_id,
                    "class_name": CLASS_NAMES.get(
                        class_id,
                        f"Unknown ({class_id})",
                    ),
                    "confidence": confidence,
                    "bbox": {
                        "x": x1,
                        "y": y1,
                        "width": x2 - x1,
                        "height": y2 - y1,
                    },
                }
            )

        return detections