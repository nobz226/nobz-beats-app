import os
import gc
import time
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

ALLOWED_AUDIO_EXTENSIONS = {'.mp3', '.wav', '.flac', '.m4a', '.aif', '.aiff', '.ogg', '.aac'}


def save_uploaded_file(file_obj, upload_folder, original_filename=None):
    """Save an uploaded file with a unique name and return the path.

    Validates the extension against ALLOWED_AUDIO_EXTENSIONS and raises
    ValueError on unsupported types.
    """
    if original_filename is None:
        original_filename = file_obj.filename

    _, ext = os.path.splitext(original_filename.lower())
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise ValueError(f"Unsupported file extension: {ext}")
        
    file_uuid, unique_filename = generate_unique_filename(original_filename)
    file_path = os.path.join(upload_folder, unique_filename)
    
    file_obj.save(file_path)
    return file_uuid, file_path

def cleanup_file(file_path):
    """Safely remove a file or directory if it exists."""
    print(f"Attempting to clean up file or directory: {file_path}")
    if os.path.exists(file_path):
        try:
            if os.path.isdir(file_path):
                shutil.rmtree(file_path, ignore_errors=True)
                print(f"Successfully removed directory: {file_path}")
            else:
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


def cleanup_expired_files(directory_path, expire_seconds):
    """Remove files and directories older than expire_seconds."""
    now = time.time()
    removed = []

    if not os.path.exists(directory_path):
        return removed

    for entry in os.listdir(directory_path):
        full_path = os.path.join(directory_path, entry)
        try:
            mtime = os.path.getmtime(full_path)
            if now - mtime > expire_seconds:
                cleanup_file(full_path)
                removed.append(full_path)
        except Exception as e:
            print(f"Error checking expiration for {full_path}: {e}")
    return removed


def _quantize_duration(beats, resolution=16):
    """Round a beat duration to the nearest musical fraction.
    
    Args:
        beats: Duration in beats
        resolution: Quantization grid (16 = 16th notes)
    
    Returns:
        Quantized duration in beats
    """
    if beats <= 0:
        return 0.0
    
    step = 1.0 / resolution
    quantized = round(beats / step) * step
    
    # Ensure minimum of 1 sixteenth note
    if quantized < step:
        quantized = step
    
    return quantized


def _clean_transcribed_notes(events, min_confidence=0.05, min_duration=0.05, max_gap=0.15):
    """Merge and filter raw transcription notes for notation output.
    
    IMPORTANT: Thresholds optimized for bass stems, which have:
    - Lower voiced probabilities (harder to detect)
    - Can have shorter note durations
    
    Args:
        events: List of note event dicts with pitch, start, duration, confidence
        min_confidence: Minimum confidence threshold (0.05 = 5% - very lenient for bass)
        min_duration: Minimum note duration in seconds (0.05 = 50ms)
        max_gap: Maximum gap to merge consecutive same pitches (0.15 = 150ms)
    
    Returns:
        Filtered and merged note events
    """
    if not events:
        return []

    print(f"_clean_transcribed_notes: Input {len(events)} events")
    
    events = sorted(events, key=lambda x: x['start'])
    cleaned = []

    # First pass: filter extremely low confidence + very short duration notes
    for idx, event in enumerate(events):
        pitch = event.get('pitch')
        duration = float(event.get('duration', 0.0))
        confidence = float(event.get('confidence', 0.0))
        start = float(event.get('start', 0.0))

        # More lenient filter for bass: keep if duration >= min_duration OR confidence >= 0.1
        if duration < min_duration and confidence < 0.1:
            print(f"  Event {idx}: FILTERED - pitch={pitch}, duration={duration:.3f}s, confidence={confidence:.3f}")
            continue

        if cleaned:
            prev = cleaned[-1]
            prev_end = prev['start'] + prev['duration']
            gap = start - prev_end
            
            # Merge adjacent same pitches with small gaps
            if prev['pitch'] == pitch and gap <= max_gap:
                print(f"  Event {idx}: MERGED with previous - pitch={pitch}, gap={gap:.3f}s")
                prev['duration'] = max(prev['duration'], prev_end - prev['start'] + gap + duration)
                prev['confidence'] = max(prev['confidence'], confidence)
                continue

        cleaned.append({'pitch': pitch, 'start': start, 'duration': duration, 'confidence': confidence})

    print(f"_clean_transcribed_notes: After first pass {len(cleaned)} events")

    # Second pass: final filtering - much more lenient
    output = []
    for idx, note_event in enumerate(cleaned):
        duration = note_event['duration']
        confidence = note_event['confidence']
        pitch = note_event['pitch']
        
        # Keep notes with reasonable duration OR reasonable confidence
        if duration < 0.05 and confidence < 0.1:
            print(f"  Final pass: FILTERED event {idx} - pitch={pitch}, duration={duration:.3f}s, confidence={confidence:.3f}")
            continue
        
        output.append(note_event)

    print(f"_clean_transcribed_notes: Output {len(output)} events")
    return output


def _estimate_tempo(y, sr, hop_length=512, fallback_bpm=120.0):
    """Estimate tempo from an audio stem for better notation grid alignment."""
    try:
        onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
        tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr, hop_length=hop_length)
        if tempo and tempo > 0:
            return float(tempo)
    except Exception as e:
        print(f"Tempo estimation failed: {e}")
    return float(fallback_bpm)


def _snap_transcribed_notes(notes, bpm, resolution=16, min_duration_beats=0.25):
    """Snap note starts and durations to a beat grid for notation.
    
    Args:
        notes: List of note events
        bpm: Tempo in beats per minute
        resolution: Grid resolution (16 = 16th notes)
        min_duration_beats: Minimum duration in beats (0.25 = 16th note)
    
    Returns:
        Snapped and merged note events
    """
    if not notes or bpm <= 0:
        print(f"_snap_transcribed_notes: Skipping - notes={len(notes) if notes else 0}, bpm={bpm}")
        return notes

    print(f"_snap_transcribed_notes: Input {len(notes)} notes at {bpm} BPM")
    
    step = 1.0 / resolution
    snapped = []

    for idx, ev in enumerate(notes):
        start_beats = ev['start'] * bpm / 60.0
        dur_beats = max(ev['duration'] * bpm / 60.0, min_duration_beats)

        snapped_start = round(start_beats / step) * step
        snapped_dur = max(round(dur_beats / step) * step, min_duration_beats)

        if snapped_start < 0:
            snapped_start = 0.0

        print(f"  Note {idx}: {ev['pitch']} - original: start={ev['start']:.3f}s dur={ev['duration']:.3f}s → snapped: start_beat={snapped_start:.3f} dur_beat={snapped_dur:.3f}")
        
        snapped.append({
            'pitch': ev['pitch'],
            'start': snapped_start * 60.0 / bpm,
            'duration': snapped_dur * 60.0 / bpm,
            'confidence': ev.get('confidence', 0.0),
        })

    print(f"_snap_transcribed_notes: After snapping {len(snapped)} notes")
    
    output = []
    for idx, event in enumerate(snapped):
        if output:
            prev = output[-1]
            prev_end = prev['start'] + prev['duration']
            gap = event['start'] - prev_end
            if prev['pitch'] == event['pitch'] and gap <= (step * 60.0 / bpm):
                print(f"  Note {idx}: MERGED {prev['pitch']} with gap {gap:.3f}s")
                prev['duration'] = (event['start'] + event['duration']) - prev['start']
                prev['confidence'] = max(prev['confidence'], event['confidence'])
                continue
        output.append(event)

    print(f"_snap_transcribed_notes: Output {len(output)} notes after merging")
    return output


def notes_to_musicxml(notes, bpm=120, time_signature='4/4'):
    """Convert a list of note events to MusicXML.
    
    Generates a valid MusicXML file from transcribed note events with improved error handling,
    better validation, and guaranteed return of valid XML.
    """
    print(f"\n{'='*80}")
    print(f"notes_to_musicxml CALLED")
    print(f"{'='*80}")
    print(f"Input: {len(notes)} notes, BPM={bpm}, time_sig={time_signature}")
    
    # CRITICAL DEBUG: Print each input note
    if notes:
        print(f"\nInput notes:")
        for idx, n in enumerate(notes):
            print(f"  {idx}: {n.get('pitch')} start={n.get('start'):.3f}s dur={n.get('duration'):.3f}s conf={n.get('confidence'):.3f}")
    else:
        print("\n⚠️  EMPTY NOTES LIST RECEIVED!")
    
    try:
        from music21 import clef, key, meter, note, stream, tempo, duration, converter
    except ImportError as e:
        print(f"ERROR: music21 is not installed: {e}")
        print("Install with: pip install music21")
        return _generate_minimal_musicxml()

    try:
        # IMPORTANT: Notes are already cleaned by transcribe_audio_file
        # Do NOT clean again - this was causing double-filtering!
        print(f"\nReceived {len(notes)} notes for MusicXML conversion (already cleaned)")
        
        if not notes:
            print("WARNING: No notes provided. Returning minimal MusicXML.")
            return _generate_minimal_musicxml()

        print(f"Creating MusicXML score with {len(notes)} notes at {bpm} BPM")

        # Create score and part with metadata
        score = stream.Score()
        part = stream.Part()
        
        # Add metadata
        part.append(tempo.MetronomeMark(number=bpm))
        part.append(meter.TimeSignature(time_signature))
        part.append(key.KeySignature(0))  # C major/A minor
        part.append(clef.TrebleClef())

        # Add notes to part with enhanced validation
        valid_note_count = 0
        skipped_notes = 0
        
        for idx, ev in enumerate(notes):
            pitch = ev.get('pitch')
            if not pitch:
                print(f"  Note {idx}: Skipping - no pitch")
                skipped_notes += 1
                continue

            start_sec = float(ev.get('start', 0.0))
            dur_sec = float(ev.get('duration', 0.0))
            
            # Validate duration
            if dur_sec <= 0:
                print(f"  Note {idx}: Skipping due to invalid duration {dur_sec}s")
                skipped_notes += 1
                continue

            # Quantize duration to musical unit
            beats = dur_sec * bpm / 60.0
            quantized = _quantize_duration(beats)
            
            if quantized <= 0:
                print(f"  Note {idx}: Skipping - quantized duration is 0 (original {beats:.3f} beats)")
                skipped_notes += 1
                continue

            # Try to create and add note
            try:
                # Convert Unicode sharps/flats to ASCII for music21
                # C♯ -> C#, D♭ -> Db, etc.
                pitch_for_m21 = pitch.replace('♯', '#').replace('♭', 'b')
                
                note_obj = note.Note(pitch_for_m21)
                # music21 Duration expects quarterLength (1.0 = quarter note)
                # quantized is in beats, so it's already in quarter notes
                note_obj.duration = duration.Duration(quarterLength=float(quantized))
                note_obj.offset = start_sec * bpm / 60.0
                part.insert(note_obj.offset, note_obj)
                # Convert offset to float for formatting (it may be a Fraction)
                offset_float = float(note_obj.offset)
                print(f"  Note {idx}: ADDED pitch={pitch_for_m21}, duration={dur_sec:.3f}s ({quantized:.3f} beats), offset={offset_float:.3f}")
                valid_note_count += 1
            except ValueError as ve:
                print(f"  Note {idx}: Invalid pitch '{pitch}' - {ve}")
                skipped_notes += 1
            except Exception as note_error:
                print(f"  Note {idx}: Error creating note '{pitch}' - {type(note_error).__name__}: {note_error}")
                skipped_notes += 1

        print(f"Added {valid_note_count} valid notes, skipped {skipped_notes}")

        # Return minimal XML if no notes were added
        if valid_note_count == 0:
            print("WARNING: No valid notes were added to score. Returning minimal MusicXML.")
            return _generate_minimal_musicxml()

        # Force music21 to create measures properly
        try:
            part.makeMeasures(inPlace=True)
            print("Measures created successfully")
        except Exception as make_measure_error:
            print(f"WARNING: Could not create measures automatically: {make_measure_error}")
            # Continue anyway - music21 can export without explicit measures

        score.append(part)

        # Export to MusicXML using music21's standard write() method
        try:
            xml_output = score.write('musicxml')
            
            # Handle different return types from music21
            if isinstance(xml_output, bytes):
                xml_output = xml_output.decode('utf-8')
            elif not isinstance(xml_output, str):
                xml_output = str(xml_output)
            
            if xml_output and len(xml_output) > 100:  # Sanity check for non-empty XML
                print(f"MusicXML export successful ({len(xml_output)} characters)")
                return xml_output
            else:
                print("WARNING: MusicXML export produced empty or invalid output")
                return _generate_minimal_musicxml_with_notes(notes, bpm, time_signature)
                
        except AttributeError:
            # Fallback if write() method doesn't exist in this version of music21
            print("INFO: score.write('musicxml') not available, trying converter module")
            try:
                xml_output = converter.write(score, fmt='musicxml')
                if isinstance(xml_output, bytes):
                    xml_output = xml_output.decode('utf-8')
                if xml_output and len(xml_output) > 100:
                    print(f"MusicXML export successful via converter ({len(xml_output)} characters)")
                    return xml_output
            except Exception as converter_error:
                print(f"Converter export failed: {converter_error}")
            
            # If both fail, generate minimal XML
            return _generate_minimal_musicxml_with_notes(notes, bpm, time_signature)
            
        except Exception as export_error:
            print(f"ERROR exporting MusicXML: {type(export_error).__name__}: {export_error}")
            print("Falling back to minimal MusicXML")
            return _generate_minimal_musicxml_with_notes(notes, bpm, time_signature)

    except Exception as e:
        print(f"CRITICAL ERROR in notes_to_musicxml: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return _generate_minimal_musicxml()


def _generate_minimal_musicxml():
    """Generate a minimal valid MusicXML document (empty score)."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<score-partwise version="3.1">\n'
        '  <part-list>\n'
        '    <score-part id="P1">\n'
        '      <part-name>Music</part-name>\n'
        '    </score-part>\n'
        '  </part-list>\n'
        '  <part id="P1">\n'
        '    <measure number="1">\n'
        '      <attributes>\n'
        '        <divisions>4</divisions>\n'
        '        <key>\n'
        '          <fifths>0</fifths>\n'
        '        </key>\n'
        '        <time>\n'
        '          <beats>4</beats>\n'
        '          <beat-type>4</beat-type>\n'
        '        </time>\n'
        '        <clef>\n'
        '          <sign>G</sign>\n'
        '          <line>2</line>\n'
        '        </clef>\n'
        '      </attributes>\n'
        '    </measure>\n'
        '  </part>\n'
        '</score-partwise>'
    )


def _generate_minimal_musicxml_with_notes(notes, bpm, time_signature):
    """Generate minimal MusicXML by manually constructing XML from note data.
    
    Used as fallback when music21 export fails.
    Properly handles note parsing and measure creation.
    """
    try:
        import xml.etree.ElementTree as ET
        from xml.dom import minidom
        
        print(f"_generate_minimal_musicxml_with_notes: Creating XML with {len(notes)} notes")
        
        # Parse time signature
        time_parts = time_signature.split('/')
        beats_per_measure = int(time_parts[0]) if len(time_parts) > 0 else 4
        beat_type = int(time_parts[1]) if len(time_parts) > 1 else 4
        
        # Create root elements
        root = ET.Element('score-partwise')
        root.set('version', '3.1')
        
        # Add part list
        part_list = ET.SubElement(root, 'part-list')
        score_part = ET.SubElement(part_list, 'score-part')
        score_part.set('id', 'P1')
        part_name = ET.SubElement(score_part, 'part-name')
        part_name.text = 'Music'
        
        # Add part with notes
        part = ET.SubElement(root, 'part')
        part.set('id', 'P1')
        
        # First measure with attributes
        measure = ET.SubElement(part, 'measure')
        measure.set('number', '1')
        
        attributes = ET.SubElement(measure, 'attributes')
        
        divisions = ET.SubElement(attributes, 'divisions')
        divisions.text = '4'
        
        key_elem = ET.SubElement(attributes, 'key')
        fifths = ET.SubElement(key_elem, 'fifths')
        fifths.text = '0'
        
        time = ET.SubElement(attributes, 'time')
        beats_elem = ET.SubElement(time, 'beats')
        beats_elem.text = str(beats_per_measure)
        beat_type_elem = ET.SubElement(time, 'beat-type')
        beat_type_elem.text = str(beat_type)
        
        clef = ET.SubElement(attributes, 'clef')
        sign = ET.SubElement(clef, 'sign')
        sign.text = 'G'
        line = ET.SubElement(clef, 'line')
        line.text = '2'
        
        # Add notes
        measure_num = 1
        current_measure = measure
        quarters_in_measure = 0.0
        max_quarters = beats_per_measure  # In 4/4: 4 quarter notes per measure
        
        for note_idx, note_data in enumerate(notes):
            # Replace Unicode sharps/flats first
            pitch_str = note_data.get('pitch', 'C4')
            pitch_str = pitch_str.replace('♯', '#').replace('♭', 'b')
            
            dur_sec = float(note_data.get('duration', 0.25))
            confidence = float(note_data.get('confidence', 0.0))
            
            # Convert duration seconds to quarter notes (accounting for divisions)
            # divisions=4 means 4 units per quarter note
            # At given BPM: seconds → beats → quarter notes → division units
            dur_quarters = max(1, round(dur_sec * bpm / 60.0 * 4))
            
            print(f"  Note {note_idx}: pitch={pitch_str}, dur={dur_sec:.3f}s → {dur_quarters} quarters")
            
            # Check if we need a new measure
            if quarters_in_measure + dur_quarters > max_quarters:
                measure_num += 1
                current_measure = ET.SubElement(part, 'measure')
                current_measure.set('number', str(measure_num))
                quarters_in_measure = 0.0
                print(f"    Starting new measure {measure_num}")
            
            # Create note element
            note_elem = ET.SubElement(current_measure, 'note')
            
            # Parse pitch (e.g., "C4" -> pitch C, octave 4)
            # Handle accidentals: C#, Db, etc.
            if len(pitch_str) > 0:
                pitch_name = pitch_str[0].upper()
                
                # Handle accidentals
                accidental = ''
                octave_start = 1
                
                if len(pitch_str) > 1 and pitch_str[1] in ['#', 'b']:
                    accidental = pitch_str[1]
                    octave_start = 2
                
                # Extract octave (everything after pitch name and optional accidental)
                pitch_octave = pitch_str[octave_start:] if octave_start < len(pitch_str) else '4'
                if not pitch_octave or not pitch_octave[0].isdigit():
                    pitch_octave = '4'  # Default to octave 4 if invalid
                
                pitch_elem = ET.SubElement(note_elem, 'pitch')
                step = ET.SubElement(pitch_elem, 'step')
                step.text = pitch_name
                
                if accidental:
                    alter = ET.SubElement(pitch_elem, 'alter')
                    alter.text = '1' if accidental == '#' else '-1'
                
                octave = ET.SubElement(pitch_elem, 'octave')
                octave.text = str(pitch_octave)
            
            duration = ET.SubElement(note_elem, 'duration')
            duration.text = str(dur_quarters)
            
            quarters_in_measure += dur_quarters
        
        print(f"_generate_minimal_musicxml_with_notes: Created {measure_num} measures")
        
        # Pretty print XML
        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent='  ')
        # Remove extra blank lines and XML declaration
        xml_lines = [line for line in xml_str.split('\n') if line.strip()]
        
        # Make sure we have XML declaration
        xml_output = '\n'.join(xml_lines)
        if not xml_output.startswith('<?xml'):
            xml_output = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_output
        
        print(f"Generated fallback MusicXML with {len(notes)} notes ({len(xml_output)} characters)")
        return xml_output
        
    except Exception as e:
        print(f"ERROR in fallback XML generation: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        # Return absolutely minimal XML
        return _generate_minimal_musicxml()


def transcribe_audio_file(file_path, hop_length=512, fmin='A0', fmax='C8'):
    """Transcribe a monophonic stem audio file into note events.
    
    Default range A0-C8 captures:
    - A0 (27.5 Hz) - lowest bass frequencies
    - C8 (4186 Hz) - high treble frequencies
    - Wide enough for all stems including bass, drums, vocals
    """
    try:
        print(f"=== TRANSCRIBE_AUDIO_FILE FUNCTION CALLED ===")
        y, sr = librosa.load(file_path, sr=22050, mono=True)
        print(f"Audio loaded for transcription, sr={sr}, length={len(y)}")

        min_hz = librosa.note_to_hz(fmin)
        max_hz = librosa.note_to_hz(fmax)
        print(f"Transcription range: {fmin} ({min_hz:.2f} Hz) to {fmax} ({max_hz:.2f} Hz)")
        print(f"Audio duration: {len(y)/sr:.2f}s")

        try:
            f0, voiced_flag, voiced_probs = librosa.pyin(
                y,
                fmin=min_hz,
                fmax=max_hz,
                sr=sr,
                hop_length=hop_length,
                frame_length=2048,
            )
        except Exception as pyin_error:
            print(f"pyin failed: {pyin_error}")
            import traceback
            traceback.print_exc()
            S = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop_length))
            pitches, magnitudes = librosa.piptrack(S=S, sr=sr, hop_length=hop_length)
            f0 = np.full(pitches.shape[1], np.nan)
            for idx in range(pitches.shape[1]):
                pitch_slice = pitches[:, idx]
                mag_slice = magnitudes[:, idx]
                if np.max(mag_slice) < 1e-6:
                    continue
                pitch = pitch_slice[np.argmax(mag_slice)]
                if pitch >= min_hz and pitch <= max_hz:
                    f0[idx] = pitch
            voiced_flag = ~np.isnan(f0)
            voiced_probs = np.where(voiced_flag, 1.0, 0.0)

        times = librosa.frames_to_time(np.arange(len(f0)), sr=sr, hop_length=hop_length)
        
        # Log pitch detection statistics
        voiced_count = np.sum(voiced_flag) if voiced_flag is not None else 0
        total_frames = len(f0)
        print(f"Pitch detection: {voiced_count}/{total_frames} frames voiced ({100*voiced_count/max(1,total_frames):.1f}%)")
        
        # Show frequency range of detected pitches
        detected_freqs = f0[~np.isnan(f0)]
        if len(detected_freqs) > 0:
            print(f"  Detected frequency range: {np.min(detected_freqs):.1f} Hz to {np.max(detected_freqs):.1f} Hz")
            detected_notes = [librosa.midi_to_note(int(round(librosa.hz_to_midi(hz)))) for hz in detected_freqs[:min(10, len(detected_freqs))]]
            print(f"  Sample detected notes: {detected_notes}")

        if len(f0) == 0:
            return {'success': True, 'notes': []}

        events = []
        current_note = None
        note_start = None
        note_confidence = None

        def _close_note(end_time):
            nonlocal current_note, note_start, note_confidence
            if current_note is None or note_start is None:
                return
            duration = max(0.0, end_time - note_start)
            if duration >= 0.05:
                events.append({
                    'pitch': current_note,
                    'start': round(float(note_start), 4),
                    'duration': round(float(duration), 4),
                    'confidence': round(float(note_confidence or 0.0), 3),
                })
            current_note = None
            note_start = None
            note_confidence = None

        # Debug: show first 20 frames of f0 and voiced_flag
        print(f"\nDEBUG: First 20 frames of pitch detection:")
        for i in range(min(20, len(f0))):
            f_hz = f0[i] if not np.isnan(f0[i]) else None
            is_voiced = voiced_flag[i] if voiced_flag is not None else False
            conf = voiced_probs[i] if voiced_probs is not None else 0.0
            note_str = librosa.midi_to_note(int(round(librosa.hz_to_midi(f_hz)))) if f_hz and f_hz > 0 else "---"
            freq_str = f"{f_hz:7.1f}" if f_hz else "   ---"
            print(f"  Frame {i:3d}: freq={freq_str}Hz ({note_str:3s}) | voiced={is_voiced} | conf={conf:.3f}")

        unvoiced_count = np.sum(~voiced_flag) if voiced_flag is not None else 0
        print(f"Unvoiced frames: {unvoiced_count}/{len(f0)} ({100*unvoiced_count/len(f0):.1f}%)")
        
        # Process frames: detect notes even from unvoiced regions if we have valid f0 values
        for i, time_sec in enumerate(times):
            # Get the f0 value regardless of voiced_flag
            hz = float(f0[i]) if not np.isnan(f0[i]) else None
            
            # If we have NO pitch estimate, close the note
            if hz is None or hz <= 0:
                _close_note(time_sec)
                continue
            
            # We have a valid pitch! Convert it to note name
            midi = librosa.hz_to_midi(hz)
            note_name = librosa.midi_to_note(int(round(midi)))
            confidence = float(voiced_probs[i]) if voiced_probs is not None else 0.0

            if note_name != current_note:
                _close_note(time_sec)
                current_note = note_name
                note_start = time_sec
                note_confidence = confidence
            else:
                note_confidence = max(note_confidence or 0.0, confidence)

        _close_note(times[-1] + librosa.frames_to_time(1, sr=sr, hop_length=hop_length))

        print(f"Raw events before cleaning: {len(events)} notes")
        if events:
            for i, evt in enumerate(events[:5]):  # Show first 5
                print(f"  Event {i}: {evt['pitch']} {evt['start']:.3f}s dur={evt['duration']:.3f}s conf={evt['confidence']:.3f}")
        
        tempo = _estimate_tempo(y, sr, hop_length=hop_length)
        events = _clean_transcribed_notes(events)
        print(f"After cleaning: {len(events)} notes")
        
        events = _snap_transcribed_notes(events, tempo)
        print(f"After snapping: {len(events)} notes")
        print(f"Transcription complete. Found {len(events)} cleaned notes at {tempo:.1f} BPM.")
        return {'success': True, 'notes': events, 'bpm': int(round(tempo))}

    except Exception as e:
        print(f"Error transcribing audio file: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


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

# --- System health checks ---

def check_system_tools():
    """Check availability of external tools (demucs, ffmpeg) and torch cache state.

    Returns a dict with booleans and small diagnostics.
    """
    import shutil
    from pathlib import Path

    demucs_path = shutil.which('demucs')
    ffmpeg_path = shutil.which('ffmpeg')

    cache_dir = Path.home() / '.cache' / 'torch' / 'hub' / 'checkpoints'
    cache_exists = cache_dir.exists() and cache_dir.is_dir()
    cache_nonempty = False
    cache_files = []
    try:
        if cache_exists:
            cache_files = [p.name for p in cache_dir.iterdir() if p.is_file()]
            cache_nonempty = len(cache_files) > 0
    except Exception as e:
        print(f"Error inspecting torch cache: {e}")

    return {
        'demucs_installed': bool(demucs_path),
        'demucs_path': demucs_path or '',
        'ffmpeg_installed': bool(ffmpeg_path),
        'ffmpeg_path': ffmpeg_path or '',
        'torch_cache_exists': cache_exists,
        'torch_cache_nonempty': cache_nonempty,
        'torch_cache_files': cache_files[:10]
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

        # Build the command as an argument list to avoid shell=True and quoting issues
        if output_format == 'mp3':
            cmd = ['ffmpeg', '-i', input_path, '-codec:a', 'libmp3lame', '-qscale:a', '2', '-y', output_path]
        elif output_format == 'wav':
            cmd = ['ffmpeg', '-i', input_path, '-codec:a', 'pcm_s16le', '-y', output_path]
        elif output_format == 'flac':
            cmd = ['ffmpeg', '-i', input_path, '-codec:a', 'flac', '-y', output_path]
        else:
            print(f"Invalid format: {output_format}")
            return False

        print(f"Command: {' '.join(cmd)}")

        # Run the command safely using subprocess.run with argument list
        print("Starting subprocess...")
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(f"Process return code: {proc.returncode}")
        if proc.returncode != 0:
            stderr_text = proc.stderr or ''
            print(f"FFmpeg error: {stderr_text}")
            return False

        # Check if the output file was created
        print(f"Checking if output file exists: {output_path}")
        if not os.path.exists(output_path):
            print(f"Output file was not created: {output_path}")
            return False

        print(f"Conversion successful: {output_path}")
        return True

    except FileNotFoundError:
        print("FFmpeg executable not found. Ensure ffmpeg is installed and in PATH.")
        return False
    except Exception as e:
        print(f"General conversion error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False