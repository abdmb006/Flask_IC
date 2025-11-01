from flask import Flask, request, render_template, jsonify
import os
import json
import subprocess

app = Flask(__name__)

CONFIG_PATH = "json/roi_config.json"
os.makedirs("json", exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/save_rois', methods=['POST'])
def save_rois():
    rois = request.get_json()
    if not rois:
        return jsonify({"message": "No ROIs received"}), 400

    for roi in rois:
        roi['x'] = int(roi['x'])
        roi['y'] = int(roi['y'])
        roi['w'] = int(roi['w'])
        roi['h'] = int(roi['h'])

    with open(CONFIG_PATH, "w") as f:
        json.dump({roi['label']: roi for roi in rois}, f, indent=4)

    return jsonify({"message": f"{len(rois)} ROIs saved successfully!"})

@app.route('/run_ocr', methods=['POST'])
def run_ocr():
    if not os.path.exists(CONFIG_PATH):
        return jsonify({"success": False, "message": "ROI config not found!"})

    # Run OCR.py as a subprocess
    try:
        # Capture output
        result = subprocess.run(['python', 'OCR.py'], capture_output=True, text=True, check=True)
        # Assume OCR.py outputs JSON
        ocr_results = json.loads(result.stdout)
        return jsonify({"success": True, "results": ocr_results})
    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "message": f"Error running OCR.py: {e.stderr}"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
