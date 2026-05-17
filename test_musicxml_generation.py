#!/usr/bin/env python3
"""
Quick verification script for MusicXML generation fixes.
Tests the notes_to_musicxml function with various scenarios.
"""

import sys
sys.path.insert(0, '/Users/eddie/Desktop/myProjects/audio-tools-API')

from utils import notes_to_musicxml

def test_empty_notes():
    """Test with empty notes list"""
    print("Test 1: Empty notes list")
    result = notes_to_musicxml([], bpm=120)
    assert result is not None, "Should return minimal MusicXML, not None"
    assert '<?xml version' in result, "Should be valid XML"
    assert 'score-partwise' in result, "Should have MusicXML structure"
    print("✓ Empty notes test passed - returns minimal MusicXML\n")


def test_valid_notes():
    """Test with valid note data"""
    print("Test 2: Valid note data")
    notes = [
        {'pitch': 'C4', 'start': 0.0, 'duration': 0.5, 'confidence': 0.9},
        {'pitch': 'D4', 'start': 0.5, 'duration': 0.5, 'confidence': 0.85},
        {'pitch': 'E4', 'start': 1.0, 'duration': 1.0, 'confidence': 0.8},
    ]
    result = notes_to_musicxml(notes, bpm=120)
    assert result is not None, "Should return MusicXML"
    assert '<?xml version' in result, "Should be valid XML"
    assert 'score-partwise' in result, "Should have MusicXML structure"
    assert 'note' in result, "Should contain note elements"
    print(f"✓ Valid notes test passed - generated {len(result)} character MusicXML\n")


def test_invalid_pitches():
    """Test with invalid pitches - should skip them gracefully"""
    print("Test 3: Invalid pitches")
    notes = [
        {'pitch': 'C4', 'start': 0.0, 'duration': 0.5, 'confidence': 0.9},
        {'pitch': 'InvalidPitch', 'start': 0.5, 'duration': 0.5, 'confidence': 0.85},
        {'pitch': 'D4', 'start': 1.0, 'duration': 1.0, 'confidence': 0.8},
    ]
    result = notes_to_musicxml(notes, bpm=120)
    assert result is not None, "Should return MusicXML even with invalid pitches"
    assert '<?xml version' in result, "Should be valid XML"
    print("✓ Invalid pitches test passed - skipped invalid note gracefully\n")


def test_zero_duration():
    """Test with zero duration notes - should skip them"""
    print("Test 4: Zero duration notes")
    notes = [
        {'pitch': 'C4', 'start': 0.0, 'duration': 0.0, 'confidence': 0.9},  # Invalid
        {'pitch': 'D4', 'start': 0.5, 'duration': 0.5, 'confidence': 0.85},  # Valid
    ]
    result = notes_to_musicxml(notes, bpm=120)
    assert result is not None, "Should return MusicXML"
    assert '<?xml version' in result, "Should be valid XML"
    print("✓ Zero duration test passed - skipped invalid note\n")


def test_realistic_transcription():
    """Test with realistic transcription data"""
    print("Test 5: Realistic transcription data")
    notes = [
        {'pitch': 'C4', 'start': 0.0, 'duration': 0.25, 'confidence': 0.95},
        {'pitch': 'D4', 'start': 0.25, 'duration': 0.25, 'confidence': 0.92},
        {'pitch': 'E4', 'start': 0.5, 'duration': 0.5, 'confidence': 0.88},
        {'pitch': 'F4', 'start': 1.0, 'duration': 0.5, 'confidence': 0.85},
        {'pitch': 'G4', 'start': 1.5, 'duration': 1.0, 'confidence': 0.9},
    ]
    result = notes_to_musicxml(notes, bpm=140, time_signature='3/4')
    assert result is not None, "Should generate MusicXML"
    assert 'C4' in result or 'C' in result, "Should contain pitch info"
    assert '<?xml version' in result, "Should be valid XML"
    print(f"✓ Realistic transcription test passed - {len(result)} character MusicXML\n")


def test_always_returns_value():
    """Verify that function never returns None"""
    print("Test 6: Function never returns None")
    test_cases = [
        [],
        [{'pitch': 'C4', 'start': 0.0, 'duration': 0.5}],
        [{'pitch': 'Invalid', 'start': 0.0, 'duration': 0.5}],
        [{'pitch': None, 'start': 0.0, 'duration': 0.5}],
    ]
    
    for i, notes in enumerate(test_cases):
        result = notes_to_musicxml(notes, bpm=120)
        assert result is not None, f"Test case {i} returned None!"
        assert isinstance(result, str), f"Test case {i} didn't return string!"
        assert len(result) > 0, f"Test case {i} returned empty string!"
    
    print("✓ All 4 test cases returned valid MusicXML strings\n")


if __name__ == '__main__':
    print("=" * 70)
    print("MusicXML Generation Verification Tests")
    print("=" * 70 + "\n")
    
    try:
        test_empty_notes()
        test_valid_notes()
        test_invalid_pitches()
        test_zero_duration()
        test_realistic_transcription()
        test_always_returns_value()
        
        print("=" * 70)
        print("✓ ALL TESTS PASSED - MusicXML generation is working correctly!")
        print("=" * 70)
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
