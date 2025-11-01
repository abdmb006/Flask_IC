import cv2
import easyocr
import json
import os
from PIL import Image

# --- Paths ---
IMAGE_PATH = "images/IC.png"
CONFIG_PATH = "json/roi_config.json"
OUTPUT_FOLDER = "outputs"
OUTPUT_IMAGE = os.path.join(OUTPUT_FOLDER, "KadPengenalan_dengan_ROI.png")
OUTPUT_JSON = "json/hasil_ocr.json"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# --- Initialize EasyOCR ---
reader = easyocr.Reader(['ms', 'en'], gpu=False)

# --- Read image ---
image = cv2.imread(IMAGE_PATH)
if image is None:
    raise FileNotFoundError(f"Image not found: {IMAGE_PATH}")

# --- Load ROI config ---
if not os.path.exists(CONFIG_PATH):
    raise FileNotFoundError(f"ROI config not found: {CONFIG_PATH}")

with open(CONFIG_PATH, "r") as f:
    rois = json.load(f)

ocr_results = {}

# --- Color map for ROI labels ---
color_map = {
    "No Kad Pengenalan": (0, 255, 0),  # Green
    "Nama": (0, 165, 255),             # Orange
    "Alamat": (0, 255, 255),           # Yellow
    "Jantina": (255, 0, 0)             # Blue
}

# --- OCR each ROI ---
for label, coords in rois.items():
    x, y, w, h = coords["x"], coords["y"], coords["w"], coords["h"]
    roi = image[y:y+h, x:x+w]

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    results = reader.readtext(gray)
    text = " ".join([res[1] for res in results])
    ocr_results[label] = text.strip() if text else "(Tiada teks dikesan)"

    # Draw ROI on image
    cv2.rectangle(image, (x, y), (x+w, y+h), color_map.get(label, (0, 255, 0)), 2)
    cv2.putText(image, label, (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_map.get(label, (0, 255, 0)), 2)

# --- Save image with ROI overlay ---
cv2.imwrite(OUTPUT_IMAGE, image)

# --- Save OCR results ---
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(ocr_results, f, ensure_ascii=False, indent=4)

print(f"OCR complete! Results saved to {OUTPUT_JSON}")
print(f"Image with ROIs saved to {OUTPUT_IMAGE}")
