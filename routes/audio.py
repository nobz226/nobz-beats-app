from flask import Blueprint, request, jsonify, current_app, send_file
import services
from utils import save_uploaded_file, cleanup_file, ALLOWED_AUDIO_EXTENSIONS
import os
import traceback

audio_bp = Blueprint('audio', __name__, url_prefix='/audio')

@audio_bp.route('/analyze', methods=['POST'])
def analyze_endpoint():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400

    audio_file = request.files['file']
    # Enforce per-request size check if present
    max_size = current_app.config.get('MAX_CONTENT_LENGTH')
    if request.content_length and max_size and request.content_length > max_size:
        return jsonify({'success': False, 'error': 'Uploaded file is too large'}), 413
    try:
        file_uuid, input_path = save_uploaded_file(audio_file, current_app.config['UPLOAD_FOLDER'])
    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 400

    try:
        result = services.analyze_audio(input_path)
        return jsonify({'success': True, 'analysis': result})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cleanup_file(input_path)

@audio_bp.route('/convert', methods=['POST'])
def convert_endpoint():
    if 'file' not in request.files or 'format' not in request.form:
        return jsonify({'success': False, 'error': 'file and format are required'}), 400

    out_format = request.form['format'].lower()
    audio_file = request.files['file']
    max_size = current_app.config.get('MAX_CONTENT_LENGTH')
    if request.content_length and max_size and request.content_length > max_size:
        return jsonify({'success': False, 'error': 'Uploaded file is too large'}), 413

    try:
        file_uuid, input_path = save_uploaded_file(audio_file, current_app.config['UPLOAD_FOLDER'])
    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 400

    try:
        converted_path = services.convert_audio(input_path, out_format, current_app.config['CONVERTED_FOLDER'])
        return send_file(converted_path, as_attachment=True)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cleanup_file(input_path)

@audio_bp.route('/separate', methods=['POST'])
def separate_endpoint():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400

    model = request.form.get('model')
    if not model:
        model = 'htdemucs'
    audio_file = request.files['file']
    max_size = current_app.config.get('MAX_CONTENT_LENGTH')
    if request.content_length and max_size and request.content_length > max_size:
        return jsonify({'success': False, 'error': 'Uploaded file is too large'}), 413

    try:
        file_uuid, input_path = save_uploaded_file(audio_file, current_app.config['UPLOAD_FOLDER'])
    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 400

    session_id = file_uuid
    output_dir = os.path.join(current_app.config['CONVERTED_FOLDER'], session_id)
    os.makedirs(output_dir, exist_ok=True)

    try:
        zip_path = services.separate_audio(input_path, output_dir, model=model)
        return send_file(zip_path, as_attachment=True)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cleanup_file(input_path)

@audio_bp.route('/test', methods=['GET'])
def test_route():
    return jsonify({'success': True, 'message': 'Audio blueprint is active'})