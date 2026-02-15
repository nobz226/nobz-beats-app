import io
import os
import tempfile
from unittest import mock

import pytest

from audio_app import app as api_app


def test_api_convert_endpoint(monkeypatch):
    client = api_app.test_client()

    # Create a temp file to act as converted output
    tmp_out = tempfile.NamedTemporaryFile(delete=False)
    tmp_out.write(b"DUMMY")
    tmp_out.flush()
    tmp_out_path = tmp_out.name
    tmp_out.close()

    # Patch the services.convert_audio to return our temp output path
    import services

    def fake_convert(input_path, target_format, out_dir):
        return tmp_out_path

    monkeypatch.setattr(services, 'convert_audio', fake_convert)

    data = {
        'file': (io.BytesIO(b"\x00\x01\x02"), 'test.wav'),
        'format': 'mp3'
    }

    resp = client.post('/api/convert', data=data, content_type='multipart/form-data')

    # We expect a successful file download response
    assert resp.status_code == 200
    # Content-Disposition should indicate attachment
    assert 'attachment' in resp.headers.get('Content-Disposition', '')

    # Clean up
    os.unlink(tmp_out_path)
