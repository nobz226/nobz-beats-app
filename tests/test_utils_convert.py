import io
import os
import subprocess
from pathlib import Path

import pytest

from utils import convert_audio


def test_convert_audio_creates_output(tmp_path, monkeypatch):
    in_file = tmp_path / "input.wav"
    out_file = tmp_path / "output.mp3"

    # Create a dummy input file
    in_file.write_bytes(b"RIFF\x00\x00\x00\x00WAVEfmt ")

    # Fake subprocess.run to simulate ffmpeg success and create output file
    def fake_run(cmd, stdout=None, stderr=None, text=False):
        # simulate ffmpeg writing the output file
        out_file.write_bytes(b"FAKE_MP3_CONTENT")
        class Result:
            returncode = 0
            stdout = ""
            stderr = ""
        return Result()

    monkeypatch.setattr(subprocess, 'run', fake_run)

    success = convert_audio(str(in_file), str(out_file), 'mp3')
    assert success is True
    assert out_file.exists()
    assert out_file.read_bytes() == b"FAKE_MP3_CONTENT"
