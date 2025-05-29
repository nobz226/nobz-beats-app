from flask import Blueprint, render_template, request, jsonify, current_app, url_for
from models import Track
from utils import analyze_audio_file, save_uploaded_file, cleanup_file
from services import AudioConversionService, StemSeparationService
import os
import sys
import traceback

# Create blueprint
audio_bp = Blueprint('audio', __name__, url_prefix='/audio')

@audio_bp.route('/analyze', methods=['GET', 'POST'])
def analyze_audio():
    """Analyze audio to detect key and tempo."""
    if request.method == 'POST':
        print("=== ANALYZE AUDIO ENDPOINT CALLED ===")
        print(f"Request files: {list(request.files.keys())}")
        
        if 'audio_file' not in request.files:
            print("No audio_file in request.files")
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        audio_file = request.files['audio_file']
        print(f"Audio file name: {audio_file.filename}")
        print(f"Audio file content type: {audio_file.content_type}")
        
        if audio_file.filename == '':
            print("Empty filename")
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        # Check file extension
        allowed_extensions = ['.mp3', '.wav', '.flac', '.mid', '.midi', '.xml', '.mxl', '.abc']
        file_ext = os.path.splitext(audio_file.filename.lower())[1]
        print(f"File extension: {file_ext}")
        
        if file_ext not in allowed_extensions:
            print(f"Unsupported file format: {file_ext}")
            return jsonify({
                'success': False,
                'error': f'Unsupported file format. Please use one of: {", ".join(allowed_extensions)}'
            }), 400
        
        try:
            # Save the uploaded file
            print("Saving uploaded file...")
            file_uuid, input_path = save_uploaded_file(audio_file, current_app.config['UPLOAD_FOLDER'])
            print(f"File saved to: {input_path}")
            
            # Free up memory from the raw audio file
            del audio_file
            import gc
            gc.collect()
            
            try:
                print("Starting audio analysis...")
                # Call the actual audio analysis function
                print("Calling analyze_audio_file function...")
                
                result = analyze_audio_file(input_path)
                print("Analysis result:", result)
                
                # Use Flask's Response object directly
                from flask import Response
                import json
                
                response = Response(
                    response=json.dumps(result),
                    status=200 if result.get('success', False) else 500,
                    mimetype="application/json"
                )
                
                return response
                
            except Exception as analysis_error:
                print(f"Analysis exception: {str(analysis_error)}")
                traceback.print_exc(file=sys.stdout)
                return jsonify({
                    'success': False,
                    'error': f"Analysis failed: {str(analysis_error)}"
                }), 500
            finally:
                # Clean up the input file
                print(f"Cleaning up input file: {input_path}")
                cleanup_file(input_path)
                
        except Exception as e:
            print(f"File handling exception: {str(e)}")
            traceback.print_exc(file=sys.stdout)
            return jsonify({
                'success': False,
                'error': f"File handling error: {str(e)}"
            }), 500
        finally:
            # Final cleanup
            import gc
            gc.collect()

    latest_track = Track.query.order_by(Track.date_added.desc()).first()
    return render_template('analyze.html', latest_track=latest_track)


@audio_bp.route('/converter', methods=['GET', 'POST'])
def converter():
    """Convert audio files between formats."""
    if request.method == 'POST':
        print("=== CONVERTER ENDPOINT CALLED ===")
        print(f"Request files: {list(request.files.keys())}")
        print(f"Request form: {list(request.form.keys())}")
        
        if 'audio_file' not in request.files:
            print("No audio_file in request.files")
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
                
        audio_file = request.files['audio_file']
        print(f"Audio file name: {audio_file.filename}")
        print(f"Audio file content type: {audio_file.content_type}")
        
        if audio_file.filename == '':
            print("Empty filename")
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        target_format = request.form.get('target_format')
        print(f"Target format: {target_format}")
        
        if target_format not in ['mp3', 'wav', 'flac']:
            print(f"Invalid format: {target_format}")
            return jsonify({
                'success': False,
                'error': 'Invalid format selected'
            }), 400

        try:
            # Initialize the conversion service
            conversion_service = AudioConversionService(
                current_app.config['UPLOAD_FOLDER'],
                current_app.config['CONVERTED_FOLDER']
            )
            
            # Use the service to convert the file
            result = conversion_service.convert_file(audio_file, target_format)
            
            # Return the result directly
            return jsonify(result)
            
        except Exception as e:
            print(f"Conversion route exception: {str(e)}")
            traceback.print_exc(file=sys.stdout)
            return jsonify({
                'success': False,
                'error': f"Conversion error: {str(e)}"
            }), 500

    latest_track = Track.query.order_by(Track.date_added.desc()).first()
    return render_template('converter.html', latest_track=latest_track)


@audio_bp.route('/separator', methods=['GET', 'POST'])
def stem_separator():
    """Separate audio into stems."""
    if request.method == 'POST':
        print("=== SEPARATOR ENDPOINT CALLED ===")
        print(f"Request files: {list(request.files.keys())}")
        
        if 'audio_file' not in request.files:
            print("No audio_file in request.files")
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        audio_file = request.files['audio_file']
        print(f"Audio file name: {audio_file.filename}")
        print(f"Audio file content type: {audio_file.content_type}")
        
        if audio_file.filename == '':
            print("Empty filename")
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
            
        # Check file extension
        allowed_extensions = ['.mp3', '.wav', '.flac', '.m4a']
        file_ext = os.path.splitext(audio_file.filename.lower())[1]
        print(f"File extension: {file_ext}")
        
        if file_ext not in allowed_extensions:
            print(f"Unsupported file format: {file_ext}")
            return jsonify({
                'success': False,
                'error': f'Unsupported file format. Please use one of: {", ".join(allowed_extensions)}'
            }), 400

        try:
            # Use the stem separation service
            separation_service = StemSeparationService(
                upload_folder=current_app.config['UPLOAD_FOLDER'],
                converted_folder=current_app.config['CONVERTED_FOLDER']
            )
            
            result = separation_service.separate_stems(audio_file)
            
            if result['success']:
                return jsonify(result)
            else:
                return jsonify(result), 500
        except Exception as e:
            print(f"Separation route exception: {str(e)}")
            traceback.print_exc(file=sys.stdout)
            return jsonify({
                'success': False,
                'error': f"Separation error: {str(e)}"
            }), 500

    latest_track = Track.query.order_by(Track.date_added.desc()).first()
    return render_template('separator.html', latest_track=latest_track)


@audio_bp.route('/cleanup_stems/<session_id>', methods=['POST'])
def cleanup_stems(session_id):
    """Clean up stem separation session files."""
    print(f"=== CLEANUP_STEMS ENDPOINT CALLED for session {session_id} ===")
    
    # Use the stem separation service
    separation_service = StemSeparationService(
        upload_folder=current_app.config['UPLOAD_FOLDER'],
        converted_folder=current_app.config['CONVERTED_FOLDER']
    )
    
    result = separation_service.cleanup_session(session_id)
    print(f"Cleanup result: {result}")
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


@audio_bp.route('/test-json', methods=['GET'])
def test_json():
    """Test route to verify JSON responses are working correctly."""
    print("=== TEST JSON ENDPOINT CALLED ===")
    return jsonify({
        'success': True,
        'message': 'JSON response is working correctly'
    })


@audio_bp.route('/test', methods=['GET'])
def test_route():
    """Test route to verify the blueprint is registered correctly."""
    print("=== TEST ROUTE CALLED ===")
    return jsonify({
        'success': True,
        'message': 'Blueprint is registered correctly'
    }) 