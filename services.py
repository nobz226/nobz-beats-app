import os
import gc
import uuid
import time
import threading
import traceback
from utils import save_uploaded_file, cleanup_file, analyze_audio_file
import utils as utils_module

# Default cleanup delay (seconds) — can be overridden with FILE_EXPIRY_SECONDS env var
CLEANUP_DELAY_SECONDS = int(os.getenv('FILE_EXPIRY_SECONDS', '900'))


def _validate_file_upload(audio_file):
    if not audio_file or not getattr(audio_file, 'filename', None):
        raise ValueError('Invalid file upload')


class AudioAnalysisService:
    """Service for handling audio analysis."""

    def __init__(self, upload_folder, converted_folder):
        self.upload_folder = upload_folder
        self.converted_folder = converted_folder

    def analyze_file(self, audio_file):
        input_path = None
        try:
            _validate_file_upload(audio_file)
            _, input_path = save_uploaded_file(audio_file, self.upload_folder)
            return analyze_audio_file(input_path)
        except ValueError as ve:
            return {'success': False, 'error': str(ve)}
        except Exception as e:
            print(f'Analysis error: {str(e)}')
            traceback.print_exc()
            return {'success': False, 'error': f'Analysis error: {str(e)}'}
        finally:
            if input_path and os.path.exists(input_path):
                cleanup_file(input_path)


class AudioConversionService:
    """Service for handling audio file conversions."""

    def __init__(self, upload_folder, converted_folder):
        self.upload_folder = upload_folder
        self.converted_folder = converted_folder

    def convert_file(self, audio_file, target_format):
        input_path = None
        output_path = None
        try:
            _validate_file_upload(audio_file)

            if target_format not in ['mp3', 'wav', 'flac']:
                return {'success': False, 'error': f'Invalid format: {target_format}'}

            _, input_path = save_uploaded_file(audio_file, self.upload_folder)
            original_name = os.path.splitext(audio_file.filename)[0]
            server_output_filename = f"{uuid.uuid4().hex}_{original_name}.{target_format}"
            output_path = os.path.join(self.converted_folder, server_output_filename)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            if not utils_module.convert_audio(input_path, output_path, target_format):
                return {'success': False, 'error': 'Conversion failed'}

            if not os.path.exists(output_path):
                return {'success': False, 'error': 'Output file not found after conversion'}

            self._schedule_file_cleanup(output_path, CLEANUP_DELAY_SECONDS)
            return {'success': True, 'output_path': output_path, 'filename': server_output_filename}
        except ValueError as ve:
            return {'success': False, 'error': str(ve)}
        except Exception as e:
            print(f'Conversion error: {str(e)}')
            traceback.print_exc()
            return {'success': False, 'error': f'Conversion error: {str(e)}'}
        finally:
            if input_path and os.path.exists(input_path):
                cleanup_file(input_path)

    def _schedule_file_cleanup(self, file_path, delay_seconds):
        def delete_file():
            time.sleep(delay_seconds)
            cleanup_file(file_path)

        cleanup_thread = threading.Thread(target=delete_file, daemon=True)
        cleanup_thread.start()


class StemSeparationService:
    """Service for handling stem separation."""

    def __init__(self, upload_folder, converted_folder):
        self.upload_folder = upload_folder
        self.converted_folder = converted_folder

    def separate_stems(self, audio_file, model='htdemucs'):
        input_path = None
        output_dir = None
        try:
            _validate_file_upload(audio_file)
            _, input_path = save_uploaded_file(audio_file, self.upload_folder)
            output_dir = os.path.join(self.converted_folder, uuid.uuid4().hex)
            os.makedirs(output_dir, exist_ok=True)

            zip_path = separate_audio(input_path, output_dir, model=model)
            self._schedule_directory_cleanup(output_dir, CLEANUP_DELAY_SECONDS)
            return {'success': True, 'zip_path': zip_path}
        except ValueError as ve:
            return {'success': False, 'error': str(ve)}
        except RuntimeError as re:
            print(f'Separation error: {str(re)}')
            traceback.print_exc()
            return {'success': False, 'error': str(re)}
        except Exception as e:
            print(f'Separation error: {str(e)}')
            traceback.print_exc()
            return {'success': False, 'error': f'Separation error: {str(e)}'}
        finally:
            if input_path and os.path.exists(input_path):
                cleanup_file(input_path)

    def _schedule_directory_cleanup(self, directory_path, delay_seconds):
        def delete_directory():
            time.sleep(delay_seconds)
            try:
                import shutil
                shutil.rmtree(directory_path, ignore_errors=True)
            except Exception as cleanup_error:
                print(f'Error cleaning up directory {directory_path}: {cleanup_error}')

        cleanup_thread = threading.Thread(target=delete_directory, daemon=True)
        cleanup_thread.start()

    def cleanup_session(self, session_id):
        try:
            output_dir = os.path.join(self.converted_folder, session_id)
            if os.path.exists(output_dir):
                import shutil
                shutil.rmtree(output_dir)
            return {'success': True}
        except Exception as e:
            print(f'Cleanup error: {str(e)}')
            traceback.print_exc()
            return {'success': False, 'error': str(e)}


# --- Convenience functional wrappers for minimal API ---

def analyze_audio(input_path):
    """Wrapper that analyzes an audio file and returns analysis results."""
    return analyze_audio_file(input_path)


def convert_audio(input_path, target_format, out_dir):
    """Convert an input file to target_format and place it in out_dir.
    Returns the path to the converted file on success, raises on failure."""
    import os
    import uuid
    from utils import convert_audio as _convert

    base = os.path.splitext(os.path.basename(input_path))[0]
    out_name = f"{base}_{uuid.uuid4().hex}.{target_format}"
    out_path = os.path.join(out_dir, out_name)

    success = _convert(input_path, out_path, target_format)
    if not success:
        raise RuntimeError(f"Conversion to {target_format} failed")
    return out_path


def separate_audio(input_path, output_dir, model='htdemucs'):
    """Run the demucs CLI to separate stems and create a zip of resulting stems.
    Returns path to the zip file.
    Requires `demucs` be available in PATH and that the demucs model is installed.
    """
    import subprocess
    import os
    import zipfile
    import re

    # Normalize model (treat empty string as default)
    model = model or 'htdemucs'

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    cmd = ['demucs', '-n', model, '-o', output_dir, '--segment', '7', '--overlap', '0.1', input_path]
    print(f"Starting Demucs stem separation with model '{model}'...")
    print(f"Command: {' '.join(cmd)}")

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        if proc.stdout is None:
            raise RuntimeError('Unable to capture Demucs output.')

        progress_pct = 0
        for line in proc.stdout:
            line = line.rstrip('\n')
            if not line:
                continue

            # Parse percentage progress from stdout lines
            match = re.search(r'(\d{1,3})\s*%|progress[:=]?\s*(\d{1,3})', line, re.IGNORECASE)
            if match:
                pct = int(match.group(1) or match.group(2))
                pct = max(0, min(100, pct))
                if pct != progress_pct:
                    progress_pct = pct
                    bar = ('#' * (pct // 2)).ljust(50, '-')
                    print(f"\r[{bar}] {progress_pct:3d}% {line}", end='', flush=True)
                    if progress_pct == 100:
                        print()
            else:
                print(line)

        proc.wait()
        if proc.returncode != 0:
            raise RuntimeError(f"Demucs failed (code {proc.returncode}). Check output above for details.")

    except FileNotFoundError:
        raise RuntimeError("Demucs CLI not found. Please install demucs and ensure it's in PATH.")

    # Zip any .wav/.mp3 files under output_dir
    zip_path = os.path.join(output_dir, 'stems.zip')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(output_dir):
            for f in files:
                if f.lower().endswith(('.wav', '.mp3')):
                    full = os.path.join(root, f)
                    arcname = os.path.relpath(full, output_dir)
                    zf.write(full, arcname)

    print(f"Demucs separation complete. Zip created at: {zip_path}")
    return zip_path
