from flask import Blueprint, request, jsonify, current_app, send_file, Response
import os
import traceback
import services
from utils import ALLOWED_AUDIO_EXTENSIONS

audio_bp = Blueprint('audio', __name__, url_prefix='/api')


def _get_extension(filename):
    _, ext = os.path.splitext(filename or '')
    return ext.lower()


def _is_valid_audio_file(file_obj):
    if not file_obj or not getattr(file_obj, 'filename', None):
        return False
    return _get_extension(file_obj.filename) in ALLOWED_AUDIO_EXTENSIONS


def _error_response(message, status_code=400):
    return jsonify({'success': False, 'error': message}), status_code


def _status_code_for_error(error_text):
    if not error_text:
        return 500
    lowered = error_text.lower()
    if any(term in lowered for term in ['invalid', 'unsupported', 'missing', 'no file']):
        return 400
    return 500


@audio_bp.route('/analyze', methods=['POST'])
def analyze_endpoint():
    if 'file' not in request.files:
        return _error_response('No file provided', 400)

    audio_file = request.files['file']
    if not _is_valid_audio_file(audio_file):
        return _error_response('Unsupported or missing audio file', 400)

    max_size = current_app.config.get('MAX_CONTENT_LENGTH')
    if request.content_length and max_size and request.content_length > max_size:
        return _error_response('Uploaded file is too large', 413)

    try:
        service = services.AudioAnalysisService(
            current_app.config['UPLOAD_FOLDER'],
            current_app.config['CONVERTED_FOLDER']
        )
        result = service.analyze_file(audio_file)
        if not result.get('success'):
            status_code = _status_code_for_error(result.get('error'))
            return _error_response(result.get('error', 'Analysis failed'), status_code)
        return jsonify({'success': True, 'analysis': result})
    except Exception as e:
        traceback.print_exc()
        return _error_response(str(e), 500)


@audio_bp.route('/convert', methods=['POST'])
def convert_endpoint():
    if 'file' not in request.files or 'format' not in request.form:
        return _error_response('file and format are required', 400)

    out_format = request.form['format'].lower()
    if out_format not in ['mp3', 'wav', 'flac']:
        return _error_response('Invalid format requested', 400)

    audio_file = request.files['file']
    if not _is_valid_audio_file(audio_file):
        return _error_response('Unsupported or missing audio file', 400)

    max_size = current_app.config.get('MAX_CONTENT_LENGTH')
    if request.content_length and max_size and request.content_length > max_size:
        return _error_response('Uploaded file is too large', 413)

    try:
        service = services.AudioConversionService(
            current_app.config['UPLOAD_FOLDER'],
            current_app.config['CONVERTED_FOLDER']
        )
        result = service.convert_file(audio_file, out_format)
        if not result.get('success'):
            status_code = _status_code_for_error(result.get('error'))
            return _error_response(result.get('error', 'Conversion failed'), status_code)
        return send_file(result['output_path'], as_attachment=True)
    except Exception as e:
        traceback.print_exc()
        return _error_response(str(e), 500)


@audio_bp.route('/separate', methods=['POST'])
def separate_endpoint():
    if 'file' not in request.files:
        return _error_response('No file provided', 400)

    audio_file = request.files['file']
    if not _is_valid_audio_file(audio_file):
        return _error_response('Unsupported or missing audio file', 400)

    model = request.form.get('model', 'htdemucs')
    max_size = current_app.config.get('MAX_CONTENT_LENGTH')
    if request.content_length and max_size and request.content_length > max_size:
        return _error_response('Uploaded file is too large', 413)

    try:
        service = services.StemSeparationService(
            current_app.config['UPLOAD_FOLDER'],
            current_app.config['CONVERTED_FOLDER']
        )
        result = service.separate_stems(audio_file, model=model)
        if not result.get('success'):
            status_code = _status_code_for_error(result.get('error'))
            return _error_response(result.get('error', 'Separation failed'), status_code)
        return send_file(result['zip_path'], as_attachment=True)
    except Exception as e:
        traceback.print_exc()
        return _error_response(str(e), 500)


@audio_bp.route('/transcribe', methods=['POST'])
def transcribe_endpoint():
    if 'file' not in request.files:
        return _error_response('No file provided', 400)

    audio_file = request.files['file']
    if not _is_valid_audio_file(audio_file):
        return _error_response('Unsupported or missing audio file', 400)

    max_size = current_app.config.get('MAX_CONTENT_LENGTH')
    if request.content_length and max_size and request.content_length > max_size:
        return _error_response('Uploaded file is too large', 413)

    try:
        service = services.AudioTranscriptionService(
            current_app.config['UPLOAD_FOLDER'],
            current_app.config['CONVERTED_FOLDER']
        )
        result = service.transcribe_file(audio_file)
        
        if not result.get('success'):
            status_code = _status_code_for_error(result.get('error'))
            return _error_response(result.get('error', 'Transcription failed'), status_code)

        output_format = request.form.get('format', '').lower()
        
        # Handle MusicXML export request
        if output_format in ['xml', 'musicxml']:
            musicxml = result.get('musicxml')
            if musicxml:
                return Response(
                    musicxml,
                    mimetype='application/xml',
                    headers={'Content-Disposition': 'attachment; filename="transcription.musicxml"'}
                )
            else:
                # MusicXML generation failed
                error_msg = result.get('musicxml_error', 'MusicXML generation failed')
                return _error_response(f'MusicXML export failed: {error_msg}', 500)

        # Default: return JSON with transcription data
        response = {
            'success': True,
            'transcription': result.get('notes', []),
        }
        
        # Include additional metadata if available
        if 'bpm' in result:
            response['bpm'] = result['bpm']
        if 'musicxml' in result:
            response['musicxml'] = result['musicxml']
        if 'musicxml_error' in result:
            response['musicxml_error'] = result['musicxml_error']
            
        return jsonify(response)
        
    except Exception as e:
        traceback.print_exc()
        return _error_response(str(e), 500)


@audio_bp.route('/test', methods=['GET'])
def test_route():
    return jsonify({'success': True, 'message': 'Audio blueprint is active'})