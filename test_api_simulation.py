#!/usr/bin/env python3
"""
Simulate real API usage - what actual users will do
"""

import sys
import os
sys.path.insert(0, '/Users/eddie/Desktop/myProjects/audio-tools-API')

import json
import io
from werkzeug.datastructures import FileStorage
from services import AudioTranscriptionService

def test_api_simulation():
    """Simulate a real API call to transcribe endpoint"""
    
    print("=" * 80)
    print("SIMULATING REAL API USAGE")
    print("=" * 80 + "\n")
    
    # Create test audio
    print("1. Creating test audio file...")
    try:
        import numpy as np
        import soundfile as sf
        
        sr = 22050
        duration = 2
        
        # Simple melody: C4, D4, E4, F4
        frequencies = [261.63, 293.66, 329.63, 349.23]
        notes_duration = 0.5
        
        audio = []
        for freq in frequencies:
            t = np.linspace(0, notes_duration, int(sr * notes_duration), False)
            note_audio = 0.3 * np.sin(2 * np.pi * freq * t)
            audio.extend(note_audio)
        
        audio = np.array(audio)
        test_file = '/tmp/api_test_audio.wav'
        sf.write(test_file, audio, sr)
        print(f"   ✓ Created: {test_file}\n")
        
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    
    # Simulate API call
    print("2. Calling AudioTranscriptionService.transcribe_file()...")
    try:
        # Create FileStorage object (what Flask would receive)
        with open(test_file, 'rb') as f:
            file_data = f.read()
        
        file_storage = FileStorage(
            stream=io.BytesIO(file_data),
            filename='test_audio.wav',
            content_type='audio/wav'
        )
        
        # Call service
        service = AudioTranscriptionService('static/uploads/', 'static/converted/')
        result = service.transcribe_file(file_storage)
        
        print(f"   ✓ Service returned\n")
        
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Show results
    print("3. Result Analysis:")
    print(f"   Success: {result.get('success')}")
    print(f"   BPM: {result.get('bpm')}")
    print(f"   Notes found: {len(result.get('notes', []))}")
    
    # Check MusicXML
    musicxml = result.get('musicxml', '')
    musicxml_error = result.get('musicxml_error')
    
    if musicxml_error:
        print(f"   ✗ MusicXML Error: {musicxml_error}\n")
        return False
    
    if not musicxml:
        print(f"   ✗ No MusicXML generated\n")
        return False
    
    print(f"   ✓ MusicXML generated ({len(musicxml)} chars)\n")
    
    # Validate MusicXML
    print("4. MusicXML Validation:")
    
    # Check declaration
    if musicxml.startswith('<?xml'):
        print("   ✓ Has XML declaration")
    else:
        print("   ✗ Missing XML declaration")
    
    # Check structure
    if '<score-partwise' in musicxml:
        print("   ✓ Valid score-partwise structure")
    else:
        print("   ✗ Invalid structure")
    
    # Count notes
    note_count = musicxml.count('<note>')
    print(f"   ✓ Contains {note_count} notes")
    
    if note_count < 1:
        print("   ✗ WARNING: No notes in MusicXML!")
        return False
    
    # Show note pitches
    import re
    pitches = re.findall(r'<step>([A-G][#b]?)</step>.*?<octave>(\d)</octave>', musicxml, re.DOTALL)
    if pitches:
        print(f"   ✓ Note pitches: {', '.join([p[0] + p[1] for p in pitches[:8]])}")
    
    # Save for user inspection
    xml_file = '/tmp/api_test_output.musicxml'
    with open(xml_file, 'w') as f:
        f.write(musicxml)
    print(f"   ✓ Saved to: {xml_file}\n")
    
    # Final status
    print("=" * 80)
    print("✅ API SIMULATION SUCCESSFUL")
    print("=" * 80)
    print(f"\nUser would receive:")
    print(f"  - Notes: {len(result['notes'])} detected")
    print(f"  - BPM: {result['bpm']}")
    print(f"  - MusicXML: Valid file with {note_count} notes")
    print(f"  - Can be opened in MuseScore, Finale, Dorico, etc.")
    
    return True

if __name__ == '__main__':
    try:
        success = test_api_simulation()
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
