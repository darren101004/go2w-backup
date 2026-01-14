from ultralytics import YOLO, YOLOWorld
from ultralytics.engine.model import Model

import logging
from PIL import Image
import io
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("yolov8_inference")

class YOLOv8Detector:
    def __init__(
        self,
        model_path: str,
        use_world: bool = True,
        custom_classes=None
    ):
        t0 = time.time()
        self.model_path = model_path
        self.use_world = use_world
        
        logger.info(f"Loading model from {self.model_path} ...")
        if use_world:
            self.model = YOLOWorld(self.model_path)
        else:
            self.model = YOLO(self.model_path)
        logger.info(f"Model loaded in {time.time() - t0:.4f}s")
        
        default_classes = list(self.model.names.values())

        self.class_names = default_classes
        if custom_classes is not None:
            self.class_names = self.class_names + list(custom_classes)
            self.model.set_classes(self.class_names)

    def detect_image(self, img_bytes: bytes | Image.Image):
        if isinstance(img_bytes, bytes):
            try:
                pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            except Exception as e:
                logger.error(f"Error loading image from bytes: {e}")
                return []
        elif isinstance(img_bytes, Image.Image):
            pil_img = img_bytes
        else:
            logger.error(f"Invalid image type: {type(img_bytes)}")
            return []

        t0 = time.time()
        results = self.model(pil_img, stream=False)
        logger.info(f"Detection done in {time.time() - t0:.4f}s")
        if not results or not hasattr(results[0], "boxes") or results[0].boxes is None:
            return []
        
        out = []
        print("Boxes: ", results[0].boxes)
        boxes_obj = results[0].boxes.xyxyn.cpu().numpy().tolist()
        class_idx = results[0].boxes.cls.cpu().numpy().tolist()
        for box, class_idx in zip(boxes_obj, class_idx):
            class_name = self.class_names[int(class_idx)] if int(class_idx) < len(self.class_names) else "unknown"
            out.append({
                "name": class_name,
                "xyxyn": box
            })
        return out

detector = YOLOv8Detector(model_path="/home/ubuntu/go2w-backup/darren_test/yolov8m.pt")
with open("/home/ubuntu/go2w-backup/darren_test/imgs/img4.jpg", "rb") as f:
    img_bytes = f.read()
detections = detector.detect_image(img_bytes)
print(detections)
