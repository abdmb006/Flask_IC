from flask import Flask, request, render_template, jsonify
import os
import json
import subprocess
import sys

app = Flask(__name__)

CONFIG_PATH = "json/roi_config.json"
IMAGE_PATH = "images/IC.png"
OUTPUT_FOLDER = "outputs"
os.makedirs("json", exist_ok=True)
os.makedirs("images", exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

PYTHON_EXE = sys.executable  # ensures same environment as Flask

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

    # Convert coordinates to integers
    for roi in rois:
        roi['x'] = int(roi['x'])
        roi['y'] = int(roi['y'])
        roi['w'] = int(roi['w'])
        roi['h'] = int(roi['h'])

    # Save ROI JSON
    with open(CONFIG_PATH, "w") as f:
        json.dump({roi['label']: roi for roi in rois}, f, indent=4)

    # Save original uploaded image
    from PIL import Image
    image = Image.open(file.stream)
    image.save(IMAGE_PATH)

    return jsonify({"message": f"{len(rois)} ROIs saved and original image saved as IC.png!"})

@app.route('/run_ocr', methods=['POST'])
def run_ocr():
    if not os.path.exists(CONFIG_PATH):
        return jsonify({"success": False, "message": "ROI config not found!"})
    if not os.path.exists(IMAGE_PATH):
        return jsonify({"success": False, "message": "Image not found!"})

    try:
        # Run OCR.py using the same Python environment
        subprocess.run([PYTHON_EXE, 'OCR.py'], capture_output=True, text=True, check=True)

        # Read hasil_ocr.json
        ocr_json_path = "json/hasil_ocr.json"
        if os.path.exists(ocr_json_path):
            with open(ocr_json_path, "r", encoding="utf-8") as f:
                ocr_results = json.load(f)
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

if __name__ == '__main__':
    print(f"Flask running with Python: {PYTHON_EXE}")
    app.run(debug=True)
