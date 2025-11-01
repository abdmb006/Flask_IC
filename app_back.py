from flask import Flask, request, render_template, send_file, jsonify
import cv2
import easyocr
import os
import json
import numpy as np
from io import BytesIO
from PIL import Image

app = Flask(__name__)
reader = easyocr.Reader(['ms', 'en'], gpu=False)

# Folder output
OUTPUT_FOLDER = "static/outputs"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Load ROI config
CONFIG_PATH = "json/roi_config_back.json"
with open(CONFIG_PATH, "r") as f:
    rois = json.load(f)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('image')
    if not file:
        return "Tiada fail diterima", 400

    # Baca imej dengan OpenCV
    in_memory_file = BytesIO()
    file.save(in_memory_file)
    data = np.frombuffer(in_memory_file.getvalue(), dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)

    # Resize imej untuk paparan
    h, w = image.shape[:2]
    scale = 900 / w
    image = cv2.resize(image, (900, int(h*scale)))

    ocr_results = {}
    color_map = {
        "No Kad Pengenalan": (0, 255, 0),
        "Nama": (0, 165, 255),
        "Alamat": (0, 255, 255),
        "Jantina": (255, 0, 0)
    }

    # OCR berdasarkan ROI config
    for label, coords in rois.items():
        x, y, w, h = coords["x"], coords["y"], coords["w"], coords["h"]
        roi = image[y:y+h, x:x+w]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        results = reader.readtext(gray)
        text = " ".join([res[1] for res in results])
        ocr_results[label] = text.strip() if text else "(Tiada teks dikesan)"

        # Lukis ROI
        cv2.rectangle(image, (x, y), (x+w, y+h), color_map.get(label, (0,255,0)), 2)
        cv2.putText(image, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_map.get(label, (0,255,0)), 2)

    # Simpan imej hasil OCR
    output_path = os.path.join(OUTPUT_FOLDER, "hasil_ocr.png")
    cv2.imwrite(output_path, image)

    return render_template('index.html', ocr_results=ocr_results, image_file=output_path)

if __name__ == '__main__':
    app.run(debug=True)
