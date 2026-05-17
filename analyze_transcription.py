#!/usr/bin/env python3
"""
Diagnostic script to analyze audio transcription with detailed frequency analysis.
Helps identify issues with bass stem transcription.
"""

import sys
import os
sys.path.insert(0, '/Users/eddie/Desktop/myProjects/audio-tools-API')

import numpy as np
import librosa

def analyze_audio_frequencies(audio_file):
    """Analyze the frequency content of an audio file"""
    
    print("=" * 80)
    print("AUDIO FREQUENCY ANALYSIS")
    print("=" * 80 + "\n")
    
    # Load audio
    y, sr = librosa.load(audio_file, sr=22050, mono=True)
    print(f"Audio file: {audio_file}")
    print(f"Sample rate: {sr} Hz")
    print(f"Duration: {len(y)/sr:.2f}s")
    print(f"Mono audio length: {len(y)} samples\n")
    
    # Compute STFT
    print("Computing frequency spectrum...")
    D = np.abs(librosa.stft(y, n_fft=2048))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    
    # Find dominant frequencies in chunks
    print("\nAnalyzing audio in 1-second chunks...")
    print("Time (s)  | Dominant Frequency | Note       | MIDI | Power\n")
    
    hop_length = 512
    chunk_size = int(sr / hop_length)  # ~1 second per chunk
    
    all_dominant_freqs = []
    
    for chunk_idx in range(0, D.shape[1], chunk_size):
        chunk = D[:, chunk_idx:chunk_idx + chunk_size]
        if chunk.shape[1] == 0:
            continue
        
        # Get average magnitude across time
        avg_mag = np.mean(chunk, axis=1)
        
        # Find peak (dominant frequency)
        peak_idx = np.argmax(avg_mag)
        dominant_freq = freqs[peak_idx]
        peak_power = avg_mag[peak_idx]
        
        # Convert to note
        if dominant_freq > 0:
            midi = librosa.hz_to_midi(dominant_freq)
            note_name = librosa.midi_to_note(int(round(midi)))
            time_sec = chunk_idx * hop_length / sr
            
            print(f"{time_sec:7.2f}  | {dominant_freq:17.1f} Hz | {note_name:10s} | {int(midi):4d} | {peak_power:.4f}")
            all_dominant_freqs.append(dominant_freq)
    
    # Summary
    if all_dominant_freqs:
        print(f"\nFrequency range: {np.min(all_dominant_freqs):.1f} - {np.max(all_dominant_freqs):.1f} Hz")
        print(f"Note range: {librosa.midi_to_note(int(librosa.hz_to_midi(np.min(all_dominant_freqs))))} to {librosa.midi_to_note(int(librosa.hz_to_midi(np.max(all_dominant_freqs))))}")
    
    return y, sr


def test_transcription_on_real_audio(audio_file):
    """Test transcription on real uploaded audio"""
    
    print("\n" + "=" * 80)
    print("TRANSCRIPTION TEST")
    print("=" * 80 + "\n")
    
    from utils import transcribe_audio_file, notes_to_musicxml
    
    print("Running transcription...\n")
    result = transcribe_audio_file(audio_file)
    
    print("\n" + "-" * 80)
    print("RESULTS")
    print("-" * 80 + "\n")
    
    success = result.get('success')
    bpm = result.get('bpm', 120)
    notes = result.get('notes', [])
    
    print(f"Transcription success: {success}")
    print(f"Detected BPM: {bpm}")
    print(f"Notes found: {len(notes)}\n")
    
    if not notes:
        print("⚠️  No notes were transcribed!")
        print("Possible issues:")
        print("  1. Audio is purely percussive (no pitched content)")
        print("  2. Frequencies are outside A0-C8 range")
        print("  3. Voiced probability too low for detection")
        print("  4. Audio quality too poor for pitch tracking")
        return False
    
    print("Detected notes:")
    for idx, note in enumerate(notes):
        print(f"  {idx}: {note['pitch']:3s} start={note['start']:7.3f}s dur={note['duration']:6.3f}s conf={note['confidence']:.3f}")
    
    # Try MusicXML generation
    print(f"\nGenerating MusicXML with {len(notes)} notes...")
    xml_output = notes_to_musicxml(notes, bpm=bpm)
    
    if xml_output:
        note_count = xml_output.count('<note>')
        print(f"✓ MusicXML generated: {len(xml_output)} chars, {note_count} notes")
        
        # Save for user
        xml_file = '/tmp/transcribed_audio.musicxml'
        with open(xml_file, 'w') as f:
            f.write(xml_output)
        print(f"✓ Saved to: {xml_file}")
        return True
    else:
        print("✗ MusicXML generation failed")
        return False


def main():
    # Check if audio file provided
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_transcription.py <audio_file>")
        print("\nExample: python3 analyze_transcription.py bass_stem.wav")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    
    if not os.path.exists(audio_file):
        print(f"Error: File not found: {audio_file}")
        sys.exit(1)
    
    # Analyze frequencies
    y, sr = analyze_audio_frequencies(audio_file)
    
    # Test transcription
    success = test_transcription_on_real_audio(audio_file)
    
    # Final summary
    print("\n" + "=" * 80)
    if success:
        print("✅ Transcription successful - check /tmp/transcribed_audio.musicxml")
    else:
        print("⚠️  Transcription produced no notes")
        print("\nDEBUGGING TIPS:")
        print("1. If frequencies shown above don't include bass:")
        print("   → Audio may be filtered or damaged")
        print("2. If frequencies are shown but no notes detected:")
        print("   → Increase frequency range (A0-C8 is already very wide)")
        print("3. If many frequencies but still no notes:")
        print("   → Lower pitch detection confidence threshold")
        print("4. If audio is percussive/drum:")
        print("   → This tool is for melodic content only")
    print("=" * 80)


if __name__ == '__main__':
    main()
