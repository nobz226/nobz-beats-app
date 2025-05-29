import os
import gc
import uuid
import shutil
import traceback
from werkzeug.utils import secure_filename
import librosa
import numpy as np

def ensure_directory_exists(directory_path):
    """Ensure a directory exists, creating it if necessary."""
    os.makedirs(directory_path, exist_ok=True)
    return directory_path

def generate_unique_filename(original_filename):
    """Generate a unique filename with UUID prefix."""
    file_uuid = str(uuid.uuid4())
    secure_name = secure_filename(original_filename)
    return file_uuid, f"{file_uuid}_{secure_name}"

def save_uploaded_file(file_obj, upload_folder, original_filename=None):
    """Save an uploaded file with a unique name and return the path."""
    if original_filename is None:
        original_filename = file_obj.filename
        
    file_uuid, unique_filename = generate_unique_filename(original_filename)
    file_path = os.path.join(upload_folder, unique_filename)
    
    file_obj.save(file_path)
    return file_uuid, file_path

def cleanup_file(file_path):
    """Safely remove a file if it exists."""
    print(f"Attempting to clean up file: {file_path}")
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"Successfully removed file: {file_path}")
            return True
        except Exception as e:
            print(f"Error cleaning up file {file_path}: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print(f"File not found for cleanup: {file_path}")
        return False

def analyze_audio_file(file_path):
    """Analyze audio file to detect tempo and key."""
    try:
        print(f"=== ANALYZE_AUDIO_FILE FUNCTION CALLED ===")
        print(f"File path: {file_path}")
        print(f"Processing file size: {os.path.getsize(file_path) / (1024 * 1024):.2f} MB")
        
        # Verify the file exists
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return {
                'success': False,
                'error': f"File not found: {file_path}"
            }
            
        # Verify the file is readable
        if not os.access(file_path, os.R_OK):
            print(f"File is not readable: {file_path}")
            return {
                'success': False,
                'error': f"File is not readable: {file_path}"
            }
            
        # Load the audio file with librosa using a lower sample rate and mono
        print(f"Loading audio file: {file_path}")
        print(f"Memory usage before loading: {gc.get_count()}")
        try:
            y, sr = librosa.load(file_path, sr=22050, mono=True)
            duration = librosa.get_duration(y=y, sr=sr)
            print(f"Audio loaded successfully, sample rate: {sr}, length: {len(y)}, duration: {duration:.2f} seconds")
        except Exception as load_error:
            print(f"Failed to load audio file: {str(load_error)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f"Failed to load audio file: {str(load_error)}"
            }
        
        # Get onset envelope with reduced complexity
        print("Calculating onset envelope")
        try:
            onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=512)
            print(f"Onset envelope calculated, length: {len(onset_env)}")
        except Exception as onset_error:
            print(f"Failed to calculate onset envelope: {str(onset_error)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f"Failed to calculate onset envelope: {str(onset_error)}"
            }
        
        # Free up memory from raw audio data
        del y
        gc.collect()
        
        # Dynamic tempo detection with simplified parameters
        print("Detecting tempo")
        try:
            # Use more comprehensive tempo detection by trying multiple starting points
            # and combining the results to avoid bias toward any particular value
            candidate_start_bpms = [60, 90, 120, 140, 180]
            all_tempos = []
            
            # Try multiple starting points to get a broader range of tempo estimates
            for start_bpm in candidate_start_bpms:
                print(f"Trying tempo detection with start_bpm={start_bpm}")
                dtempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr, aggregate=None,
                                           hop_length=512, start_bpm=start_bpm)
                all_tempos.extend(dtempo)
                print(f"  Found {len(dtempo)} tempo estimates")
            
            print(f"Tempo candidates collected, count: {len(all_tempos)}")
        except Exception as tempo_error:
            print(f"Failed to detect tempo: {str(tempo_error)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f"Failed to detect tempo: {str(tempo_error)}"
            }
        
        # Calculate tempos more efficiently and improve the clustering
        try:
            # Convert to numpy array for easier manipulation
            all_tempos = np.array(all_tempos)
            
            # Group tempos that are close to each other (within 3 BPM)
            grouped_tempos = []
            for tempo in all_tempos:
                # Check if this tempo is close to any existing group
                found_group = False
                for i, (group_tempo, count) in enumerate(grouped_tempos):
                    if abs(tempo - group_tempo) < 3:
                        # Update the group with weighted average
                        new_tempo = (group_tempo * count + tempo) / (count + 1)
                        grouped_tempos[i] = (new_tempo, count + 1)
                        found_group = True
                        break
                
                # If no close group found, create a new one
                if not found_group:
                    grouped_tempos.append((tempo, 1))
            
            # Sort by count (frequency)
            grouped_tempos.sort(key=lambda x: x[1], reverse=True)
            print(f"Grouped tempos: {grouped_tempos[:5]}")
            
            # Consider tempo harmonics (double or half the tempo)
            tempo_candidates = []
            for tempo, count in grouped_tempos:
                # Create score including harmonics
                harmonic_counts = sum(c for t, c in grouped_tempos if abs(t - tempo/2) < 3 or abs(t - tempo*2) < 3)
                tempo_candidates.append((tempo, count + harmonic_counts))
            
            # Sort by score
            tempo_candidates.sort(key=lambda x: x[1], reverse=True)
            print(f"Tempo candidates with harmonics: {tempo_candidates[:5]}")
        except Exception as tempo_calc_error:
            print(f"Failed to calculate tempo frequencies: {str(tempo_calc_error)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f"Failed to calculate tempo frequencies: {str(tempo_calc_error)}"
            }
        
        # Free up memory
        del onset_env
        del all_tempos
        gc.collect()
        
        # Get the best tempo
        if not tempo_candidates:
            print("No tempo candidates found, using default 120 BPM")
            best_tempo = 120  # Default if no tempo detected
        else:
            best_tempo = tempo_candidates[0][0]
            print(f"Best tempo: {best_tempo} BPM")
        
        # Load audio again for key detection with very low duration
        print("Detecting key")
        key = "Unknown"  # Default value
        try:
            y, sr = librosa.load(file_path, sr=22050, duration=30, mono=True)
            print(f"Audio reloaded for key detection, sample rate: {sr}, length: {len(y)}")
            
            # Improved key detection using Krumhansl-Schmuckler key-finding algorithm
            chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=512, n_chroma=12)
            chroma_norm = np.mean(chroma, axis=1)
            
            # Major and minor profile templates from music theory (Krumhansl-Kessler profiles)
            major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
            minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
            
            # Normalize profiles
            major_profile = major_profile / np.sum(major_profile)
            minor_profile = minor_profile / np.sum(minor_profile)
            
            # Compute correlation for all possible key shifts
            key_scores = []
            key_names_major = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            key_names_minor = ['Cm', 'C#m', 'Dm', 'D#m', 'Em', 'Fm', 'F#m', 'Gm', 'G#m', 'Am', 'A#m', 'Bm']
            
            # Compute correlation for all major keys
            for i in range(12):
                # Shift the profile
                shifted_profile = np.roll(major_profile, i)
                # Compute correlation
                corr = np.corrcoef(chroma_norm, shifted_profile)[0, 1]
                key_scores.append((key_names_major[i], corr))
            
            # Compute correlation for all minor keys
            for i in range(12):
                # Shift the profile
                shifted_profile = np.roll(minor_profile, i)
                # Compute correlation
                corr = np.corrcoef(chroma_norm, shifted_profile)[0, 1]
                key_scores.append((key_names_minor[i], corr))
            
            # Sort by correlation (highest first)
            key_scores.sort(key=lambda x: x[1], reverse=True)
            print(f"Top key candidates: {key_scores[:3]}")
            
            # Get the most likely key
            key = key_scores[0][0]
            print(f"Key detected: {key}")
            
            # Clean up
            del y
            del chroma
        except Exception as key_error:
            print(f"Error detecting key: {str(key_error)}")
            import traceback
            traceback.print_exc()
            # Continue with the default key value
        
        gc.collect()
        
        print(f"Analysis complete: Tempo={best_tempo:.2f} BPM, Key={key}")
        return {
            'success': True,
            'tempo': int(round(float(best_tempo))),
            'key': key
        }
    
    except Exception as e:
        print(f"Error during audio analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': f"Error analyzing audio: {str(e)}"
        }

def convert_audio(input_path, output_path, output_format):
    """Convert audio file to specified format using ffmpeg."""
    import subprocess
    import os
    
    try:
        print(f"=== CONVERT_AUDIO FUNCTION CALLED ===")
        print(f"Input path: {input_path}")
        print(f"Output path: {output_path}")
        print(f"Output format: {output_format}")
        
        # Ensure the output directory exists
        output_dir = os.path.dirname(output_path)
        print(f"Ensuring output directory exists: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)
        
        # Build the command as a single string
        if output_format == 'mp3':
            cmd = f'ffmpeg -i "{input_path}" -codec:a libmp3lame -qscale:a 2 -y "{output_path}"'
        elif output_format == 'wav':
            cmd = f'ffmpeg -i "{input_path}" -codec:a pcm_s16le -y "{output_path}"'
        elif output_format == 'flac':
            cmd = f'ffmpeg -i "{input_path}" -codec:a flac -y "{output_path}"'
        else:
            print(f"Invalid format: {output_format}")
            return False
        
        print(f"Command: {cmd}")
        
        # Run the command with shell=True
        print("Starting subprocess...")
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for the process to complete
        print("Waiting for process to complete...")
        stdout, stderr = process.communicate()
        
        # Check if the process was successful
        print(f"Process return code: {process.returncode}")
        if process.returncode != 0:
            stderr_text = stderr.decode('utf-8', errors='replace')
            print(f"FFmpeg error: {stderr_text}")
            return False
        
        # Check if the output file was created
        print(f"Checking if output file exists: {output_path}")
        if not os.path.exists(output_path):
            print(f"Output file was not created: {output_path}")
            return False
            
        print(f"Conversion successful: {output_path}")
        return True
    except Exception as e:
        print(f"General conversion error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False 