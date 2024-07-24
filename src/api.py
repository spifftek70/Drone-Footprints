from flask import Flask, request, jsonify
import subprocess
from Utils.logger_config import logger
import json
import time
from pathlib import Path
import threading

app = Flask(__name__)

@app.route('/run_script', methods=['POST'])
def run_script():
    data = request.get_json()
    logger.info(f"Received payload: {data}")
    outer_path = data['outputPath']
    Path(outer_path).mkdir(parents=True, exist_ok=True)

    args = ["python", "/usr/src/app/Drone_Footprints.py", "-o", outer_path, "-i", data['inputPath']]
    
    # Conditional arguments
    if data.get('declination'):
        args.append("-d")
    if data.get('cog'):
        args.append("-c")
    if data.get('lense_correction'):
        args.append("-l")
    if data.get('image_equalize'):
        args.append("-z")
    if data.get('dsmFile'):
        args.extend(["-v", data['dsmFile']])
    elif data.get('elevation_service'):
        args.append("-m")
    if data.get('sensorWidth'):
        args.extend(["-w", str(data['sensorWidth'])])  # Convert to string
    if data.get('sensorHeight'):
        args.extend(["-t", str(data['sensorHeight'])])  # Convert to string
    if data.get('nodejs'):
        args.append("-n")
    else:
        args.append("-y")

    process = subprocess.run(args, capture_output=True, text=True)
    if process.returncode != 0:
        return jsonify({'status': 'error', 'message': process.stderr}), 500
    return jsonify({'status': 'success', 'message': process.stdout})

@app.errorhandler(Exception)
def handle_error(e):
    logger.error(f"An error occurred: {str(e)}")
    return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Now start the Flask application
    app.run(host='0.0.0.0', port=5050, debug=True)
