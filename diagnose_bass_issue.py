#!/usr/bin/env python3
"""
Deep diagnostic script to analyze bass stem transcription.
Run with: python3 diagnose_bass_issue.py <path_to_bass_stem>
"""

import sys
import os
sys.path.insert(0, '/Users/eddie/Desktop/myProjects/audio-tools-API')

import json

def test_transcription_chain(audio_file):
    """Test the complete transcription chain with detailed output"""
    
    print("\n" + "="*80)
    print("DEEP DIAGNOSTIC: BASS STEM TRANSCRIPTION ANALYSIS")
    print("="*80 + "\n")
    
    print(f"Audio file: {audio_file}")
    print(f"File size: {os.path.getsize(audio_file) / (1024*1024):.2f} MB\n")
    
    # Import after adding to path
    from utils import transcribe_audio_file, notes_to_musicxml
    from services import AudioTranscriptionService
    from werkzeug.datastructures import FileStorage
    import io
    
    print("STEP 1: Call transcribe_audio_file directly")
    print("-" * 80)
    result = transcribe_audio_file(audio_file)
    
    success = result.get('success')
    notes_count = len(result.get('notes', []))
    bpm = result.get('bpm', 120)
    
    print(f"\nResult:")
    print(f"  Success: {success}")
    print(f"  Notes: {notes_count}")
    print(f"  BPM: {bpm}\n")
    
    notes = result.get('notes', [])
    if notes:
        print(f"First 10 notes:")
        for i, n in enumerate(notes[:10]):
            print(f"  {i}: {n['pitch']:3s} start={n['start']:7.3f}s dur={n['duration']:6.3f}s conf={n['confidence']:.3f}")
    else:
        print("⚠️  NO NOTES DETECTED BY TRANSCRIBE_AUDIO_FILE!\n")
        print("Possible issues:")
        print("  1. Audio is purely percussive (no pitched content)")
        print("  2. All frames marked as 'unvoiced' by pyin")
        print("  3. Pitch detection failed or audio is damaged")
        return False
    
    print("\n" + "="*80)
    print("STEP 2: Call notes_to_musicxml with the transcribed notes")
    print("-" * 80)
    
    xml_output = notes_to_musicxml(notes, bpm=bpm)
    
    print(f"\nXML Result:")
    print(f"  XML size: {len(xml_output) if xml_output else 0} characters")
    
    if not xml_output:
        print("  ✗ MusicXML generation returned None!")
        return False
    
    if '<?xml' in xml_output:
        print("  ✓ Has XML declaration")
    else:
        print("  ✗ Missing XML declaration")
    
    if '<note>' in xml_output:
        note_count_in_xml = xml_output.count('<note>')
        print(f"  ✓ Contains {note_count_in_xml} note elements")
    else:
        print("  ✗ NO NOTE ELEMENTS IN XML!")
    
    # Save XML for inspection
    xml_file = '/tmp/bass_diagnostic.musicxml'
    with open(xml_file, 'w') as f:
        f.write(xml_output)
    print(f"\nXML saved to: {xml_file}\n")
    
    print("="*80)
    print("STEP 3: Simulate API endpoint call")
    print("-" * 80)
    
    try:
        # Simulate file upload
        with open(audio_file, 'rb') as f:
            file_data = f.read()
        
        file_storage = FileStorage(
            stream=io.BytesIO(file_data),
            filename=os.path.basename(audio_file),
            content_type='audio/wav'
        )
        
        # Call service
        service = AudioTranscriptionService('/tmp', '/tmp')
        service_result = service.transcribe_file(file_storage)
        
        print(f"\nService result:")
        print(f"  Success: {service_result.get('success')}")
        
        service_notes = service_result.get('notes', [])
        print(f"  Notes count: {len(service_notes)}")
        
        service_xml = service_result.get('musicxml', '')
        print(f"  MusicXML size: {len(service_xml)} characters")
        
        if service_xml:
            note_count_api = service_xml.count('<note>')
            print(f"  Notes in XML: {note_count_api}")
            if note_count_api == 0:
                print("\n⚠️  CRITICAL: API generated XML with 0 notes!")
                print("     This is the bug!")
            else:
                print(f"\n✓ API working correctly - {note_count_api} notes in XML")
        else:
            print("\n✗ No MusicXML in response")
            error = service_result.get('musicxml_error')
            if error:
                print(f"  Error: {error}")
        
    except Exception as e:
        print(f"\nError calling service: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Transcription: {notes_count} notes detected")
    print(f"Direct XML generation: {'✓' if '<note>' in xml_output else '✗'} {xml_output.count('<note>')} notes")
    print(f"Service API: {'✓' if service_xml else '✗'} {service_xml.count('<note>')} notes")
    
    return True


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 diagnose_bass_issue.py <bass_stem_file>")
        print("\nExample: python3 diagnose_bass_issue.py ~/Downloads/bass_stem.wav")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    
    if not os.path.exists(audio_file):
        print(f"Error: File not found: {audio_file}")
        sys.exit(1)
    
    success = test_transcription_chain(audio_file)
    
    if not success:
        print("\n✗ Diagnostic failed")
        sys.exit(1)
