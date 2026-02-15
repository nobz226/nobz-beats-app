from flask import Flask, request, jsonify, send_file
import os
import uuid
from config import config
from utils import ensure_directory_exists, save_uploaded_file, cleanup_file
import services

# Minimal Flask app focused on audio tools: analyzer, converter, separator
app = Flask(__name__)

# Load configuration (development by default)
app_config = config['default']
app.config.from_object(app_config)
app_config.init_app(app)

# Ensure folders exist
ensure_directory_exists(app.config['UPLOAD_FOLDER'])
ensure_directory_exists(app.config['CONVERTED_FOLDER'])
# Enforce maximum upload size (Flask will reject requests larger than this)
app.config['MAX_CONTENT_LENGTH'] = getattr(app_config, 'MAX_CONTENT_LENGTH', app.config.get('MAX_CONTENT_LENGTH'))

@app.route('/')
def index():
    return jsonify({'success': True, 'message': 'NOBZ BEATS - Audio Tools API (analyze, convert, separate)'}), 200

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'}), 400

    f = request.files['file']
    try:
        file_uuid, filepath = save_uploaded_file(f, app.config['UPLOAD_FOLDER'])
    except ValueError as ve:
        return jsonify({'success': False, 'message': str(ve)}), 400

    try:
        result = services.analyze_audio(filepath)
        return jsonify({'success': True, 'analysis': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cleanup_file(filepath)

@app.route('/api/convert', methods=['POST'])
def api_convert():
    if 'file' not in request.files or 'format' not in request.form:
        return jsonify({'success': False, 'message': 'file and format are required'}), 400

    out_format = request.form['format'].lower()
    f = request.files['file']
    try:
        file_uuid, filepath = save_uploaded_file(f, app.config['UPLOAD_FOLDER'])
    except ValueError as ve:
        return jsonify({'success': False, 'message': str(ve)}), 400

    try:
        converted_path = services.convert_audio(filepath, out_format, app.config['CONVERTED_FOLDER'])
        return send_file(converted_path, as_attachment=True)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cleanup_file(filepath)

@app.route('/api/separate', methods=['POST'])
def api_separate():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'}), 400

    model = request.form.get('model', 'htdemucs')
    f = request.files['file']

    try:
        file_uuid, filepath = save_uploaded_file(f, app.config['UPLOAD_FOLDER'])
    except ValueError as ve:
        return jsonify({'success': False, 'message': str(ve)}), 400

    session_id = str(uuid.uuid4())
    output_dir = os.path.join(app.config['CONVERTED_FOLDER'], session_id)
    ensure_directory_exists(output_dir)

    try:
        zip_path = services.separate_audio(filepath, output_dir, model=model)
        return send_file(zip_path, as_attachment=True)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cleanup_file(filepath)

if __name__ == '__main__':
    app.run(debug=True, port=5002)
