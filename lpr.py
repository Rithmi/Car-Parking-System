"""
License Plate Recognition (LPR) module with best-frame selection and AI detection.
Supports both contour-based and optional YOLOv8 plate detection.
"""

import re
import cv2
import numpy as np
import easyocr
from typing import Tuple, Optional, List

# Initialize EasyOCR reader (CPU only)
reader = easyocr.Reader(['en'], gpu=False)
ALLOWLIST = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
PROVINCE_CODES = {"WP", "CP", "SP", "NP", "EP", "NW", "NC", "SB", "UP", "NE"}

# Try to import YOLOv8 for advanced plate detection
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
    YOLO_MODEL_PATH = "yolov8m.pt"
except ImportError:
    YOLO_AVAILABLE = False
    YOLO_MODEL_PATH = None


def normalize_plate(plate_text: str) -> str:
    """Normalize plate: uppercase, remove spaces/hyphens, keep alphanumerics."""
    plate = plate_text.upper().strip()
    plate = re.sub(r"[^A-Z0-9]", "", plate)
    return plate


def detect_motion(frame1: np.ndarray, frame2: np.ndarray, threshold: int = 1000) -> bool:
    """Detect motion between two frames using frame differencing."""
    if frame1 is None or frame2 is None:
        return False
    
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(gray1, gray2)
    motion_pixels = cv2.countNonZero(cv2.threshold(diff, 50, 255, cv2.THRESH_BINARY)[1])
    
    return motion_pixels > threshold


def score_frame_quality(frame: np.ndarray) -> float:
    """Score frame quality: Laplacian variance + normalized brightness."""
    if frame is None or frame.size == 0:
        return 0.0
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Laplacian variance (sharpness)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    
    # Brightness (normalized to 0-1)
    brightness = np.mean(gray) / 255.0
    brightness_penalty = abs(brightness - 0.5) * 2
    brightness_score = 1.0 - brightness_penalty
    
    # Combined score (60% sharpness, 40% brightness)
    sharpness_score = min(1.0, laplacian_var / 500.0)
    
    quality = 0.6 * sharpness_score + 0.4 * brightness_score
    return max(0.0, min(1.0, quality))


def select_best_frame(frames: List[np.ndarray]) -> Tuple[Optional[np.ndarray], int]:
    """Select best frame from buffer based on quality."""
    if not frames:
        return None, -1
    
    best_score = -1
    best_idx = 0
    
    for i, frame in enumerate(frames):
        score = score_frame_quality(frame)
        if score > best_score:
            best_score = score
            best_idx = i
    
    return frames[best_idx], best_idx


def detect_plate_roi_contour(frame: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    """Detect license plate ROI using contour-based method (more lenient)."""
    try:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
        gray = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
        
        contours, _ = cv2.findContours(gray, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        h, w = gray.shape
        
        for contour in contours:
            x, y, cw, ch = cv2.boundingRect(contour)
            aspect_ratio = cw / float(ch) if ch > 0 else 0
            area = cw * ch
            
            # RELAXED: More lenient aspect ratio and area constraints
            # Originally: 2.0 < aspect_ratio < 8.0 and 1000 < area < (h * w * 0.5)
            if 1.0 < aspect_ratio < 10.0 and 500 < area < (h * w * 0.5):
                return (x, y, cw, ch)
        
        return None
    except Exception:
        return None


def detect_plate_roi_yolo(frame: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    """Detect license plate ROI using YOLOv8 (if available)."""
    if not YOLO_AVAILABLE:
        return None
    
    try:
        if not hasattr(detect_plate_roi_yolo, '_model'):
            detect_plate_roi_yolo._model = YOLO(YOLO_MODEL_PATH)
        
        model = detect_plate_roi_yolo._model
        results = model.predict(frame, conf=0.5, verbose=False)
        
        if results and len(results) > 0:
            detections = results[0].boxes
            if detections and len(detections) > 0:
                sorted_dets = sorted(
                    [(b.xyxy[0], b.conf) for b in detections],
                    key=lambda x: x[1],
                    reverse=True
                )
                
                if sorted_dets:
                    xyxy, _ = sorted_dets[0]
                    x1, y1, x2, y2 = map(int, xyxy)
                    return (x1, y1, x2 - x1, y2 - y1)
        
        return None
    except Exception as e:
        print(f"[lpr] YOLO error: {e}")
        return None


def detect_plate_roi(frame: np.ndarray, use_yolo: bool = True) -> Optional[Tuple[int, int, int, int]]:
    """Detect plate ROI with optional YOLO fallback to contours."""
    if use_yolo:
        roi = detect_plate_roi_yolo(frame)
        if roi:
            return roi
    
    return detect_plate_roi_contour(frame)


def crop_plate_region(frame: np.ndarray, roi: Tuple[int, int, int, int], padding: int = 10) -> np.ndarray:
    """Crop plate region from frame with padding."""
    x, y, w, h = roi
    h_frame, w_frame = frame.shape[:2]
    
    x1 = max(0, x - padding)
    y1 = max(0, y - padding)
    x2 = min(w_frame, x + w + padding)
    y2 = min(h_frame, y + h + padding)
    
    return frame[y1:y2, x1:x2]


def ocr_read_all(gray_img: np.ndarray) -> List[Tuple[str, float, float]]:
    """Run EasyOCR. Returns list of (text, confidence, y_center)."""
    try:
        results = reader.readtext(
            gray_img,
            detail=1,
            paragraph=False,
            allowlist=ALLOWLIST,
            decoder="beamsearch"
        )
        
        items = []
        for (bbox, text, conf) in results:
            t = text.upper().strip()
            t = re.sub(r"[^A-Z0-9]", "", t)
            if not t:
                continue
            
            ys = [p[1] for p in bbox]
            y_center = sum(ys) / len(ys)
            items.append((t, float(conf), y_center))
        
        return items
    except Exception as e:
        print(f"[lpr] OCR error: {e}")
        return []


def build_plate_from_ocr(items: List[Tuple[str, float, float]]) -> Tuple[str, float]:
    """Construct license plate from OCR items (Sri Lanka: 2-3 letters + 4 digits)."""
    if not items:
        return "", 0.0
    
    items_sorted = sorted(items, key=lambda x: x[2])
    ys = [it[2] for it in items_sorted]
    y_median = np.median(ys) if ys else 0
    
    top = [it for it in items_sorted if it[2] <= y_median]
    bottom = [it for it in items_sorted if it[2] > y_median]
    
    # FIXED: Now searches for 2-3 letters instead of exactly 2
    def find_letters(s): 
        m = re.search(r"[A-Z]{2,3}", s)
        return m.group(0) if m else ""
    
    def find_digits(s):
        m = re.search(r"\d{4}", s)
        return m.group(0) if m else ""
    
    best_letters = ""
    best_letters_conf = 0.0
    
    # Try to find registration letters (exclude province codes)
    for t, conf, _ in top:
        letters = find_letters(t)
        if letters and letters not in PROVINCE_CODES and conf > best_letters_conf:
            best_letters = letters
            best_letters_conf = conf
    
    # Fallback: accept any letters if none found
    if not best_letters:
        for t, conf, _ in top:
            letters = find_letters(t)
            if letters and conf > best_letters_conf:
                best_letters = letters
                best_letters_conf = conf
    
    best_digits = ""
    best_digits_conf = 0.0
    
    # Try to find digits in bottom section
    for t, conf, _ in bottom:
        digits = find_digits(t)
        if digits and conf > best_digits_conf:
            best_digits = digits
            best_digits_conf = conf
    
    # Fallback: search entire image for digits
    if not best_digits:
        for t, conf, _ in items_sorted:
            digits = find_digits(t)
            if digits and conf > best_digits_conf:
                best_digits = digits
                best_digits_conf = conf
    
    if best_letters and best_digits:
        final_conf = (best_letters_conf + best_digits_conf) / 2.0
        return f"{best_letters}{best_digits}", final_conf
    
    # Last resort: look for 2-3 letters + 4 digits pattern in OCR text
    for t, conf, _ in items_sorted:
        m = re.search(r"([A-Z]{2,3})(\d{4})", t)
        if m and m.group(1) not in PROVINCE_CODES:
            return f"{m.group(1)}{m.group(2)}", conf
    
    return "", 0.0


def preprocess_variants(gray: np.ndarray) -> List[np.ndarray]:
    """Generate multiple preprocessing variants for OCR."""
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    
    return [
        gray,
        cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
        cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1],
        cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 7),
    ]


def read_plate_from_frame(frame: np.ndarray, use_yolo: bool = YOLO_AVAILABLE) -> Tuple[str, float]:
    """Main entry point: detect ROI, extract region, run OCR. Falls back to full frame if ROI fails."""
    if frame is None or frame.size == 0:
        return "", 0.0
    
    try:
        # Try to detect plate ROI
        roi = detect_plate_roi(frame, use_yolo=use_yolo)
        
        # If ROI detected, crop it; otherwise use entire frame
        if roi:
            plate_crop = crop_plate_region(frame, roi, padding=5)
        else:
            # FALLBACK: Use entire frame if ROI detection fails
            plate_crop = frame
        
        gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
        
        best_plate, best_conf = "", 0.0
        
        for preprocessed in preprocess_variants(gray):
            items = ocr_read_all(preprocessed)
            plate, conf = build_plate_from_ocr(items)
            if plate and conf > best_conf:
                best_plate = plate
                best_conf = conf
        
        return normalize_plate(best_plate), best_conf
    
    except Exception as e:
        print(f"[lpr] read_plate error: {e}")
        return "", 0.0


def read_plate_from_image(image_path: str) -> Tuple[str, float]:
    """Read license plate from an image file."""
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Could not read image: {image_path}")
        return "", 0.0
    
    return read_plate_from_frame(img)
