import os
import subprocess

from utils import convert_audio, cleanup_file, cleanup_expired_files


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


def test_cleanup_expired_files_removes_old_entries(tmp_path):
    converted_dir = tmp_path / 'converted'
    converted_dir.mkdir()
    old_file = converted_dir / 'old.mp3'
    old_dir = converted_dir / 'old_dir'
    old_dir.mkdir()
    (old_dir / 'stem.wav').write_bytes(b'hi')

    old_file.write_bytes(b'old')
    old_time = 0
    os.utime(old_file, (old_time, old_time))
    os.utime(old_dir, (old_time, old_time))

    removed = cleanup_expired_files(str(converted_dir), expire_seconds=1)

    assert str(old_file) in removed
    assert str(old_dir) in removed
    assert not old_file.exists()
    assert not old_dir.exists()
