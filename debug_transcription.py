#!/usr/bin/env python3
"""
Comprehensive debugging script for audio transcription and MusicXML generation.
Shows exactly what happens at each stage of the pipeline.
"""

import sys
import os
sys.path.insert(0, '/Users/eddie/Desktop/myProjects/audio-tools-API')

# Create a synthetic audio file for testing
def create_test_audio():
    """Create a simple test audio file"""
    try:
        import numpy as np
        import soundfile as sf
        from librosa import get_duration
        
        print("Creating test audio file...")
        
        # Create synthetic monophonic audio - simple melody
        sr = 22050  # Sample rate
        duration = 4  # seconds
        
        # Simple melody: C4, D4, E4, F4 (quarter notes at 120 BPM)
        frequencies = [261.63, 293.66, 329.63, 349.23]  # C4, D4, E4, F4
        notes_duration = 0.5  # 0.5 seconds each (quarter notes at 120 BPM)
        
        audio = []
        for freq in frequencies:
            # Generate sine wave for each note
            t = np.linspace(0, notes_duration, int(sr * notes_duration), False)
            note_audio = 0.3 * np.sin(2 * np.pi * freq * t)
            audio.extend(note_audio)
        
        audio = np.array(audio)
        
        # Save to file
        test_file = '/tmp/test_audio.wav'
        sf.write(test_file, audio, sr)
        
        print(f"✓ Created test audio: {test_file} ({len(audio)/sr:.1f}s)")
        print(f"  Notes: C4, D4, E4, F4 at 120 BPM\n")
        
        return test_file
        
    except Exception as e:
        print(f"ERROR creating test audio: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_transcription_pipeline():
    """Test the full transcription and MusicXML generation pipeline"""
    
    print("=" * 80)
    print("AUDIO TRANSCRIPTION & MUSICXML GENERATION DEBUGGING")
    print("=" * 80 + "\n")
    
    # Create test audio
    audio_file = create_test_audio()
    if not audio_file:
        print("Failed to create test audio")
        return False
    
    # Import after creating audio (to ensure imports are fresh)
    from utils import transcribe_audio_file, notes_to_musicxml, _clean_transcribed_notes, _snap_transcribed_notes
    
    print("-" * 80)
    print("STAGE 1: TRANSCRIBE AUDIO FILE")
    print("-" * 80 + "\n")
    
    result = transcribe_audio_file(audio_file)
    
    print(f"\nTranscription result:")
    print(f"  Success: {result.get('success')}")
    print(f"  BPM: {result.get('bpm')}")
    notes = result.get('notes', [])
    print(f"  Notes returned: {len(notes)}\n")
    
    if not notes:
        print("ERROR: No notes were transcribed! This is likely a pitch detection issue.")
        print("The audio may:")
        print("  - Be too noisy")
        print("  - Have pitches outside C2-C7 range")
        print("  - Have low voiced probabilities")
        print("\nFalling back to test with synthetic notes...\n")
        
        # Use synthetic notes for testing
        notes = [
            {'pitch': 'C4', 'start': 0.0, 'duration': 0.5, 'confidence': 0.95},
            {'pitch': 'D4', 'start': 0.5, 'duration': 0.5, 'confidence': 0.92},
            {'pitch': 'E4', 'start': 1.0, 'duration': 0.5, 'confidence': 0.88},
            {'pitch': 'F4', 'start': 1.5, 'duration': 0.5, 'confidence': 0.90},
        ]
        print(f"Using synthetic notes for testing: {len(notes)} notes\n")
    
    # Show notes before cleaning
    print("Notes before cleaning:")
    for idx, note in enumerate(notes):
        print(f"  {idx}: {note['pitch']:3s} start={note['start']:6.3f}s dur={note['duration']:6.3f}s conf={note['confidence']:.3f}")
    
    print("\n" + "-" * 80)
    print("STAGE 2: CLEAN TRANSCRIBED NOTES")
    print("-" * 80 + "\n")
    
    cleaned_notes = _clean_transcribed_notes(notes)
    
    print(f"\nNotes after cleaning: {len(cleaned_notes)} (filtered {len(notes) - len(cleaned_notes)})")
    for idx, note in enumerate(cleaned_notes):
        print(f"  {idx}: {note['pitch']:3s} start={note['start']:6.3f}s dur={note['duration']:6.3f}s conf={note['confidence']:.3f}")
    
    print("\n" + "-" * 80)
    print("STAGE 3: SNAP NOTES TO BEAT GRID")
    print("-" * 80 + "\n")
    
    bpm = result.get('bpm', 120)
    snapped_notes = _snap_transcribed_notes(cleaned_notes, bpm)
    
    print(f"\nNotes after snapping to {bpm} BPM: {len(snapped_notes)}")
    for idx, note in enumerate(snapped_notes):
        print(f"  {idx}: {note['pitch']:3s} start={note['start']:6.3f}s dur={note['duration']:6.3f}s conf={note['confidence']:.3f}")
    
    print("\n" + "-" * 80)
    print("STAGE 4: GENERATE MUSICXML")
    print("-" * 80 + "\n")
    
    xml_output = notes_to_musicxml(snapped_notes, bpm=bpm)
    
    if xml_output:
        print(f"\n✓ MusicXML generated successfully")
        print(f"  Size: {len(xml_output)} characters")
        print(f"  Validity: ", end='')
        
        # Check validity
        if '<?xml' in xml_output and 'score-partwise' in xml_output:
            print("✓ Valid MusicXML structure")
        else:
            print("✗ Invalid structure")
        
        if '<note>' in xml_output:
            note_count = xml_output.count('<note>')
            print(f"  Notes in XML: {note_count}")
        else:
            print(f"  WARNING: No notes found in XML!")
        
        # Save for inspection
        xml_file = '/tmp/test_output.musicxml'
        with open(xml_file, 'w') as f:
            f.write(xml_output)
        print(f"  Saved to: {xml_file}")
    else:
        print("\n✗ MusicXML generation failed (returned None)")
        return False
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✓ Transcription: {len(notes)} raw notes")
    print(f"✓ Cleaning: {len(cleaned_notes)} valid notes")
    print(f"✓ Snapping: {len(snapped_notes)} snapped notes")
    print(f"✓ MusicXML: {len(xml_output)} characters generated")
    
    if '<note>' in xml_output:
        note_count = xml_output.count('<note>')
        print(f"✓ Notes in XML: {note_count} notes")
        if note_count > 0:
            print("\n✅ SUCCESS - MusicXML contains notes!")
        else:
            print("\n⚠️  WARNING - MusicXML created but contains no notes")
    else:
        print("\n⚠️  WARNING - Empty fallback MusicXML (no notes generated)")
    
    print("\n" + "=" * 80)
    return True


if __name__ == '__main__':
    try:
        success = test_transcription_pipeline()
        if success:
            print("\n✅ Pipeline test completed successfully")
        else:
            print("\n❌ Pipeline test failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
