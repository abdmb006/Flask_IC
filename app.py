from flask import Flask, request, render_template, jsonify, send_from_directory
import os
import json
import subprocess
import sys
from PIL import Image, UnidentifiedImageError

app = Flask(__name__)

CONFIG_PATH = "json/roi_config.json"
IMAGE_PATH = "images/IC.png"
OUTPUT_FOLDER = "outputs"
OUTPUT_IMAGE = os.path.join(OUTPUT_FOLDER, "KadPengenalan_dengan_ROI.png")
OUTPUT_JSON = "json/hasil_ocr.json"

os.makedirs("json", exist_ok=True)
os.makedirs("images", exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

PYTHON_EXE = sys.executable

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/save_rois', methods=['POST'])
def save_rois():
    rois = request.form.get('rois')
    file = request.files.get('image')

    if not rois or not file:
        return jsonify({"message": "Missing ROIs or image!"}), 400

    rois = json.loads(rois)

    for roi in rois:
        roi['x'] = int(roi['x'])
        roi['y'] = int(roi['y'])
        roi['w'] = int(roi['w'])
        roi['h'] = int(roi['h'])

    with open(CONFIG_PATH, "w") as f:
        json.dump({roi['label']: roi for roi in rois}, f, indent=4)

    # Ensure the file is a valid image
    try:
        image = Image.open(file.stream).convert("RGB")
        image.save(IMAGE_PATH)
    except UnidentifiedImageError:
        return jsonify({"message": "Cannot identify image file. Please upload a valid image!"}), 400

    return jsonify({"message": f"{len(rois)} ROIs saved and original image saved as IC.png!"})

@app.route('/run_ocr', methods=['POST'])
def run_ocr():
    if not os.path.exists(CONFIG_PATH):
        return jsonify({"success": False, "message": "ROI config not found!"})
    if not os.path.exists(IMAGE_PATH):
        return jsonify({"success": False, "message": "Image not found!"})

    try:
        subprocess.run([PYTHON_EXE, 'OCR.py'], capture_output=True, text=True, check=True)

        if os.path.exists(OUTPUT_JSON):
            with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
                ocr_results = json.load(f)
            ocr_results['output_image'] = OUTPUT_IMAGE.replace("\\", "/")
            return jsonify({"success": True, "results": ocr_results})
        else:
            return jsonify({"success": False, "message": "hasil_ocr.json not found!"})

    except subprocess.CalledProcessError as e:
        return jsonify({
            "success": False,
            "message": f"Error running OCR.py:\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/outputs/<path:filename>')
def serve_output_image(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

if __name__ == '__main__':
    print(f"Flask running with Python: {PYTHON_EXE}")
    app.run(debug=True)
