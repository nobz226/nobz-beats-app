import io
import os
import tempfile
from unittest import mock

import pytest

from audio_app import app as api_app


def test_api_convert_endpoint(monkeypatch):
    client = api_app.test_client()

    tmp_out = tempfile.NamedTemporaryFile(delete=False)
    tmp_out.write(b"DUMMY")
    tmp_out.flush()
    tmp_out_path = tmp_out.name
    tmp_out.close()

    import services

    def fake_convert(input_path, output_path, output_format):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'wb') as out_file:
            out_file.write(b'DUMMY')
        return True

    monkeypatch.setattr(services.utils_module, 'convert_audio', fake_convert)

    data = {
        'file': (io.BytesIO(b"\x00\x01\x02"), 'test.wav'),
        'format': 'mp3'
    }

    resp = client.post('/api/convert', data=data, content_type='multipart/form-data')

    assert resp.status_code == 200
    assert 'attachment' in resp.headers.get('Content-Disposition', '')

    os.unlink(tmp_out_path)


def test_api_analyze_endpoint_requires_file():
    client = api_app.test_client()
    resp = client.post('/api/analyze', data={}, content_type='multipart/form-data')
    assert resp.status_code == 400
    assert resp.json['success'] is False
    assert 'No file provided' in resp.json['error']


def test_api_separate_endpoint_requires_file():
    client = api_app.test_client()
    resp = client.post('/api/separate', data={}, content_type='multipart/form-data')
    assert resp.status_code == 400
    assert resp.json['success'] is False
    assert 'No file provided' in resp.json['error']
