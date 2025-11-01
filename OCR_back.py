import cv2
import easyocr
import json
import os
import matplotlib.pyplot as plt

# --- Fail imej & konfigurasi ROI ---
IMAGE_PATH = "images/IC.png"
CONFIG_PATH = "json/roi_config.json"

# --- Inisialisasi EasyOCR (guna CPU sahaja, elak warning CUDA) ---
reader = easyocr.Reader(['ms', 'en'], gpu=False)

# --- Fungsi resize untuk paparan seragam ---
def resize_with_aspect_ratio(img, width=None, height=None):
    (h, w) = img.shape[:2]
    if width is None and height is None:
        return img
    if width is not None:
        r = width / float(w)
        dim = (width, int(h * r))
    else:
        r = height / float(h)
        dim = (int(w * r), height)
    return cv2.resize(img, dim, interpolation=cv2.INTER_AREA)

# --- Baca imej ---
image = cv2.imread(IMAGE_PATH)
if image is None:
    raise FileNotFoundError(f"Imej tidak dijumpai di: {IMAGE_PATH}")

image = resize_with_aspect_ratio(image, width=900)

# --- Semak jika ROI sudah disimpan ---
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r") as f:
        rois = json.load(f)
    print(f"📂 ROI config dimuat dari {CONFIG_PATH}")
else:
    print("🖱 Tiada konfigurasi ROI. Sila pilih kawasan ROI (4 kali):\n")
    labels = ["No Kad Pengenalan", "Nama", "Alamat", "Jantina"]
    rois = {}
    for label in labels:
        print(f"Pilih kawasan untuk: {label}")
        r = cv2.selectROI("Pilih ROI", image)
        cv2.destroyWindow("Pilih ROI")
        x, y, w, h = map(int, r)
        rois[label] = {"x": x, "y": y, "w": w, "h": h}
        print(f"{label}: {r}")
    with open(CONFIG_PATH, "w") as f:
        json.dump(rois, f, indent=4)
    print("✅ ROI disimpan ke roi_config.json")

# --- OCR setiap ROI ---
print("\n📖 Membaca teks menggunakan EasyOCR...\n")

ocr_results = {}
for label, coords in rois.items():
    x, y, w, h = coords["x"], coords["y"], coords["w"], coords["h"]
    roi = image[y:y+h, x:x+w]

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    results = reader.readtext(gray)
    text = " ".join([res[1] for res in results])
    ocr_results[label] = text.strip() if text else "(Tiada teks dikesan)"

    print(f"🟩 {label}: {ocr_results[label]}")

    # Simpan imej potongan ROI
    # cv2.imwrite(f"{label.replace(' ', '_')}.png", roi)

    # Lukis ROI di imej asal
    color_map = {
        "No Kad Pengenalan": (0, 255, 0),  # Hijau
        "Nama": (0, 165, 255),             # Oren
        "Alamat": (0, 255, 255),           # Kuning
        "Jantina": (255, 0, 0)             # Biru
    }
    cv2.rectangle(image, (x, y), (x+w, y+h), color_map.get(label, (0, 255, 0)), 2)
    cv2.putText(image, label, (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_map.get(label, (0, 255, 0)), 2)

# --- Simpan imej hasil OCR ---
output_path = "outputs/KadPengenalan_dengan_ROI.png"
cv2.imwrite(output_path, image)
print(f"\n💾 Imej hasil disimpan sebagai: {output_path}")

# --- Simpan teks OCR ke fail JSON ---
with open("json/hasil_ocr.json", "w", encoding="utf-8") as f:
    json.dump(ocr_results, f, ensure_ascii=False, indent=4)
print("🧾 Hasil OCR disimpan dalam fail: json/hasil_ocr.json")

# --- Papar imej dalam PyCharm dengan matplotlib ---
# plt.figure(figsize=(12, 8))
# plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
# plt.title("Kad Pengenalan dengan ROI")
# plt.axis("off")
# plt.show()
