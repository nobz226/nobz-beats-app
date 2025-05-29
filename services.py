import os
import gc
import uuid
import time
import threading
import torch
from flask import url_for
from utils import save_uploaded_file, cleanup_file, convert_audio

class AudioConversionService:
    """Service for handling audio file conversions."""
    
    def __init__(self, upload_folder, converted_folder):
        self.upload_folder = upload_folder
        self.converted_folder = converted_folder
    
    def convert_file(self, audio_file, target_format):
        """Convert an uploaded audio file to the target format."""
        input_path = None
        output_path = None
        
        try:
            print("=== CONVERT_FILE METHOD CALLED ===")
            # Validate input
            if not audio_file or not hasattr(audio_file, 'filename') or not audio_file.filename:
                print("Invalid file: audio_file is None or has no filename")
                return {
                    'success': False,
                    'error': 'Invalid file'
                }
                
            # Validate target format
            if target_format not in ['mp3', 'wav', 'flac']:
                print(f"Invalid format: {target_format}")
                return {
                    'success': False,
                    'error': f'Invalid format: {target_format}'
                }
            
            # Save the uploaded file
            print(f"Saving uploaded file: {audio_file.filename}")
            file_uuid, input_path = save_uploaded_file(audio_file, self.upload_folder)
            print(f"File saved to: {input_path}")
            
            # Verify the file was saved
            if not os.path.exists(input_path):
                print(f"File not saved: {input_path}")
                return {
                    'success': False,
                    'error': 'Failed to save uploaded file'
                }
            
            # Create output path
            original_filename = audio_file.filename
            original_name = os.path.splitext(original_filename)[0]
            output_filename = f"{original_name}.{target_format}"  # User-friendly name
            server_output_filename = f"{file_uuid}_{output_filename}"  # Server storage name
            output_path = os.path.join(self.converted_folder, server_output_filename)
            print(f"Output path: {output_path}")
            
            # Ensure the output directory exists
            print(f"Ensuring output directory exists: {os.path.dirname(output_path)}")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Convert the file
            print(f"Converting file from {input_path} to {output_path}")
            if convert_audio(input_path, output_path, target_format):
                # Verify the output file was created
                if not os.path.exists(output_path):
                    print(f"Output file not created: {output_path}")
                    return {
                        'success': False,
                        'error': 'Conversion completed but output file not found'
                    }
                
                print(f"File converted successfully: {output_path}")
                
                # Generate download URL - use a direct approach without url_for
                try:
                    # Hardcode the URL path
                    download_url = f"/static/converted/{server_output_filename}"
                    print(f"Generated URL: {download_url}")
                except Exception as url_error:
                    print(f"Error generating URL: {str(url_error)}")
                    import traceback
                    traceback.print_exc()
                    return {
                        'success': False,
                        'error': f'Error generating download URL: {str(url_error)}'
                    }
                
                # Schedule cleanup
                print(f"Scheduling cleanup for: {output_path}")
                self._schedule_file_cleanup(output_path, 15)  # 15 seconds
                
                return {
                    'success': True,
                    'download_url': download_url,
                    'filename': output_filename
                }
            else:
                print("Conversion failed")
                return {
                    'success': False,
                    'error': 'Conversion failed'
                }
        
        except Exception as e:
            print(f"Conversion error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f'Conversion error: {str(e)}'
            }
        
        finally:
            # Clean up input file
            if input_path and os.path.exists(input_path):
                print(f"Cleaning up input file: {input_path}")
                cleanup_file(input_path)
    
    def _schedule_file_cleanup(self, file_path, delay_seconds):
        """Schedule a file for deletion after a delay."""
        def delete_file():
            time.sleep(delay_seconds)
            cleanup_file(file_path)
        
        cleanup_thread = threading.Thread(target=delete_file)
        cleanup_thread.daemon = True
        cleanup_thread.start()


class StemSeparationService:
    """Service for handling stem separation."""
    
    def __init__(self, upload_folder, converted_folder):
        self.upload_folder = upload_folder
        self.converted_folder = converted_folder
    
    def separate_stems(self, audio_file):
        """Separate an audio file into stems."""
        import demucs.separate
        
        input_path = None
        
        try:
            # Save the uploaded file
            file_uuid, input_path = save_uploaded_file(audio_file, self.upload_folder)
            output_dir = file_uuid + "_" + os.path.splitext(os.path.basename(input_path))[0]
            
            # Clear memory
            del audio_file
            gc.collect()
            
            # Configure demucs for separation
            demucs.separate.main([
                "--mp3",
                "-n", "htdemucs",
                "--segment", "7",
                "-d", "cpu",
                "--overlap", "0.1",
                "--out", self.converted_folder,
                input_path
            ])
            
            # Generate URLs for stems
            stem_paths = {}
            source_stems = ['drums', 'bass', 'vocals', 'other']
            display_stems = ['drums', 'bass', 'vocals', 'melody']
            
            # Find output directory
            possible_dirs = [
                output_dir,
                file_uuid,
                os.path.splitext(os.path.basename(input_path))[0]
            ]
            
            found_dir = None
            for dir_name in possible_dirs:
                check_path = os.path.join(self.converted_folder, 'htdemucs', dir_name)
                if os.path.exists(check_path):
                    found_dir = dir_name
                    break
            
            if not found_dir:
                raise Exception("Output directory not found")
            
            # Get stem URLs
            for source_stem, display_stem in zip(source_stems, display_stems):
                stem_filename = f"{source_stem}.mp3"
                full_path = os.path.join(self.converted_folder, 'htdemucs', found_dir, stem_filename)
                if os.path.exists(full_path):
                    relative_path = os.path.join('htdemucs', found_dir, stem_filename)
                    stem_paths[display_stem] = url_for('static', filename=f'converted/{relative_path}')
            
            # Force garbage collection
            gc.collect()
            try:
                if hasattr(torch, 'cuda') and torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception as e:
                print(f"Warning: Could not clear CUDA cache: {str(e)}")
            
            return {
                'success': True,
                'stems': stem_paths,
                'session_id': found_dir
            }
            
        except Exception as e:
            print(f"Separation error: {str(e)}")
            import traceback
            print(f"Full error details: {traceback.format_exc()}")
            return {
                'success': False,
                'error': 'Failed to process audio file. Please try again with a different file.'
            }
        finally:
            # Clean up input file regardless of success or failure
            if input_path and os.path.exists(input_path):
                print(f"Cleaning up input file: {input_path}")
                cleanup_file(input_path)
    
    def cleanup_session(self, session_id):
        """Clean up stem separation session files."""
        try:
            print(f"=== CLEANUP_SESSION METHOD CALLED for session {session_id} ===")
            output_dir = os.path.join(self.converted_folder, 'htdemucs', session_id)
            print(f"Checking if directory exists: {output_dir}")
            
            if os.path.exists(output_dir):
                print(f"Directory exists, removing: {output_dir}")
                import shutil
                shutil.rmtree(output_dir)
                print(f"Successfully removed directory: {output_dir}")
                return {'success': True}
            
            print(f"Directory does not exist: {output_dir}")
            return {'success': True, 'message': 'Directory already cleaned'}
        except Exception as e:
            print(f"Cleanup error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)} 