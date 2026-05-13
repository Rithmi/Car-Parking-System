import re
import cv2
import numpy as np
import easyocr

reader = easyocr.Reader(['en'], gpu=False)
ALLOWLIST = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

PROVINCE_CODES = {"WP", "CP", "SP", "NP", "EP", "NW", "NC", "SB", "UP", "NE"}

def clean_text(text: str) -> str:
    text = text.upper()
    text = re.sub(r"[^A-Z0-9]", "", text)
    return text

def find_two_letters(s: str) -> str:
    m = re.search(r"[A-Z]{2}", s)
    return m.group(0) if m else ""

def find_four_digits(s: str) -> str:
    m = re.search(r"\d{4}", s)
    return m.group(0) if m else ""

def ocr_read_all(gray_img):
    """
    Returns list of items:
    (text_clean, conf, y_center)
    """
    results = reader.readtext(
        gray_img,
        detail=1,
        paragraph=False,
        allowlist=ALLOWLIST,
        decoder="beamsearch"
    )

    items = []
    for (bbox, text, conf) in results:
        t = clean_text(text)
        if not t:
            continue

        # bbox = [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
        ys = [p[1] for p in bbox]
        y_center = sum(ys) / len(ys)
        items.append((t, float(conf), y_center))

    return items

def build_sl_plate_from_items(items):
    """
    Sri Lanka plate style in your image:
      Top line has letters (QL)
      Bottom line has digits (9904)
    We ignore province codes like SP/WP/CP.
    """
    if not items:
        return "", 0.0

    # Sort by vertical position (top to bottom)
    items_sorted = sorted(items, key=lambda x: x[2])

    # Split into top-half and bottom-half based on median y
    ys = [it[2] for it in items_sorted]
    y_median = np.median(ys)

    top = [it for it in items_sorted if it[2] <= y_median]
    bottom = [it for it in items_sorted if it[2] > y_median]

    # 1) Get letters from TOP (prefer non-province)
    best_letters = ""
    best_letters_conf = 0.0

    for (t, conf, _y) in top:
        letters = find_two_letters(t)
        if letters and letters not in PROVINCE_CODES and conf > best_letters_conf:
            best_letters = letters
            best_letters_conf = conf

    # If no non-province letters, fallback to any letters in top
    if not best_letters:
        for (t, conf, _y) in top:
            letters = find_two_letters(t)
            if letters and conf > best_letters_conf:
                best_letters = letters
                best_letters_conf = conf

    # 2) Get digits from BOTTOM
    best_digits = ""
    best_digits_conf = 0.0

    for (t, conf, _y) in bottom:
        digits = find_four_digits(t)
        if digits and conf > best_digits_conf:
            best_digits = digits
            best_digits_conf = conf

    # If bottom didn’t work, try anywhere
    if not best_digits:
        for (t, conf, _y) in items_sorted:
            digits = find_four_digits(t)
            if digits and conf > best_digits_conf:
                best_digits = digits
                best_digits_conf = conf

    if best_letters and best_digits:
        # confidence = average of the two parts
        final_conf = (best_letters_conf + best_digits_conf) / 2.0
        return f"{best_letters} {best_digits}", final_conf

    # Fallback: try direct pattern in any text
    best_plate = ""
    best_conf = 0.0
    for (t, conf, _y) in items_sorted:
        m = re.search(r"([A-Z]{2})(\d{4})", t)
        if m:
            letters = m.group(1)
            digits = m.group(2)
            # prefer non-province
            if letters in PROVINCE_CODES:
                continue
            if conf > best_conf:
                best_plate = f"{letters} {digits}"
                best_conf = conf

    return best_plate, best_conf

def preprocess(gray):
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    variants = [
        gray,
        cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
        cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1],
        cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                              cv2.THRESH_BINARY, 31, 7),
        cv2.filter2D(gray, -1, np.array([[0, -1, 0],
                                         [-1, 5, -1],
                                         [0, -1, 0]], dtype=np.float32))
    ]
    return variants

def read_plate_from_frame(img) -> tuple[str, float]:
    if img is None:
        return "", 0.0

    # Avoid upscaling frames: large upscales dramatically increase memory
    # and cause PyTorch to allocate very large tensors. Instead, only
    # downscale very large images to a reasonable maximum size and keep
    # smaller images at native resolution.
    h, w = img.shape[:2]
    max_dim = max(h, w)
    MAX_DIM = 1024
    if max_dim > MAX_DIM:
        scale = MAX_DIM / float(max_dim)
        new_w = int(w * scale)
        new_h = int(h * scale)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    best_plate, best_conf = "", 0.0

    try:
        for v in preprocess(gray):
            items = ocr_read_all(v)
            plate, conf = build_sl_plate_from_items(items)

            if plate and conf > best_conf:
                best_plate = plate
                best_conf = conf
    except RuntimeError as e:
        # Catch PyTorch/CUDA OOM or allocator errors and fail gracefully.
        print(f"[lpr] OCR RuntimeError: {e}")
        return "", 0.0
    except Exception as e:
        print(f"[lpr] OCR exception: {e}")
        return "", 0.0

    return best_plate, best_conf

def read_plate_from_image(image_path: str) -> tuple[str, float]:
    """
    Read license plate from an image file.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        (plate_text, confidence_score)
    """
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Could not read image: {image_path}")
        return "", 0.0
    
    return read_plate_from_frame(img)
