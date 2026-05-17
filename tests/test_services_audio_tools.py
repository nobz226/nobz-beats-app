import os
import tempfile
import zipfile

import services


class DummyUpload:
    def __init__(self, filename, content=b'hello'):
        self.filename = filename
        self._content = content

    def save(self, dst):
        with open(dst, 'wb') as fp:
            fp.write(self._content)


def test_audio_analysis_service_returns_result(tmp_path, monkeypatch):
    upload_dir = tmp_path / 'uploads'
    converted_dir = tmp_path / 'converted'
    upload_dir.mkdir()
    converted_dir.mkdir()

    fake_file = DummyUpload('track.wav', b'FAKE WAV DATA')

    monkeypatch.setattr(services, 'analyze_audio_file', lambda path: {'success': True, 'tempo': 120, 'key': 'C'})

    service = services.AudioAnalysisService(str(upload_dir), str(converted_dir))
    result = service.analyze_file(fake_file)

    assert result['success'] is True
    assert result['tempo'] == 120
    assert result['key'] == 'C'
    assert len(list(upload_dir.iterdir())) == 0


def test_audio_conversion_service_rejects_invalid_format(tmp_path):
    upload_dir = tmp_path / 'uploads'
    converted_dir = tmp_path / 'converted'
    upload_dir.mkdir()
    converted_dir.mkdir()

    fake_file = DummyUpload('track.wav', b'FAKE WAV DATA')
    service = services.AudioConversionService(str(upload_dir), str(converted_dir))

    result = service.convert_file(fake_file, 'exe')

    assert result['success'] is False
    assert 'Invalid format' in result['error']
    assert len(list(upload_dir.iterdir())) == 0


def test_audio_conversion_service_creates_output_path(tmp_path, monkeypatch):
    upload_dir = tmp_path / 'uploads'
    converted_dir = tmp_path / 'converted'
    upload_dir.mkdir()
    converted_dir.mkdir()

    fake_file = DummyUpload('track.wav', b'FAKE WAV DATA')
    output_path = converted_dir / 'converted.mp3'

    def fake_convert(input_path, out_path, format_name):
        with open(out_path, 'wb') as out_file:
            out_file.write(b'FAKE_MP3_CONTENT')
        return True

    monkeypatch.setattr(services.utils_module, 'convert_audio', fake_convert)

    service = services.AudioConversionService(str(upload_dir), str(converted_dir))
    result = service.convert_file(fake_file, 'mp3')

    assert result['success'] is True
    assert 'output_path' in result
    assert os.path.exists(result['output_path'])
    with open(result['output_path'], 'rb') as fp:
        assert fp.read() == b'FAKE_MP3_CONTENT'


def test_stem_separation_service_returns_zip_path(tmp_path, monkeypatch):
    upload_dir = tmp_path / 'uploads'
    converted_dir = tmp_path / 'converted'
    upload_dir.mkdir()
    converted_dir.mkdir()

    fake_file = DummyUpload('track.wav', b'FAKE WAV DATA')

    def fake_separate(input_path, output_dir, model='htdemucs'):
        zip_path = os.path.join(output_dir, 'stems.zip')
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('drums.mp3', 'fake')
        return zip_path

    monkeypatch.setattr(services, 'separate_audio', fake_separate)

    service = services.StemSeparationService(str(upload_dir), str(converted_dir))
    result = service.separate_stems(fake_file, model='htdemucs')

    assert result['success'] is True
    assert os.path.exists(result['zip_path'])
    assert zipfile.is_zipfile(result['zip_path'])


def test_audio_transcription_service_returns_notes(tmp_path, monkeypatch):
    upload_dir = tmp_path / 'uploads'
    converted_dir = tmp_path / 'converted'
    upload_dir.mkdir()
    converted_dir.mkdir()

    fake_file = DummyUpload('stem.wav', b'FAKE STEM DATA')

    def fake_transcribe(input_path):
        return {'success': True, 'notes': [{'pitch': 'C4', 'start': 0.0, 'duration': 0.5, 'confidence': 0.9}]}

    monkeypatch.setattr(services, 'transcribe_audio_file', fake_transcribe)

    service = services.AudioTranscriptionService(str(upload_dir), str(converted_dir))
    result = service.transcribe_file(fake_file)

    assert result['success'] is True
    assert result['notes'][0]['pitch'] == 'C4'
    assert 'musicxml' in result
    assert '<score-partwise' in result['musicxml']
    assert len(list(upload_dir.iterdir())) == 0
