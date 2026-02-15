# Audio Tools API (by Nobz)

This repository provides a small, self-contained Flask-based API exposing three audio tools useful for building audio applications:

- Audio analysis (tempo/BPM and musical key detection)
- Audio format conversion (MP3, WAV, FLAC)
- Stem separation (vocals, drums, bass, melody) using Demucs

This project is intended to be an open-source developer-focused API that other applications can call to integrate audio processing features. Anyone may download, modify, and redistribute this code according to the license (see the `License` section).

Contents
- Overview
- Requirements
- Quick start (macOS / Linux)
- Configuration
- Running the API
- Endpoints and examples
- File lifecycle and cleanup
- Development notes and recommendations
- Troubleshooting
- Security considerations
- Contributing and License

Overview
--------

The codebase is organized with a clear separation of concerns:

- `app.py` — Main Flask application that registers routes and blueprints.
- `routes/audio.py` — Blueprint exposing the HTTP API endpoints for audio tools.
- `services.py` — Service-layer helpers and higher-level wrappers.
- `utils.py` — File I/O, audio analysis, FFmpeg-based conversion, health checks.
- `config.py` — Basic runtime configuration (upload and converted folders).

Requirements
------------

Python dependencies are listed in `requirements.txt`. This project also depends on system tools:

- Python 3.8 or newer
- System `ffmpeg` (install via `brew install ffmpeg` on macOS)
- Demucs (either Python package or CLI; see notes below)

Note on PyTorch and Demucs:
- `demucs` and `torch` may require platform-specific wheels. On macOS, you may want to install a compatible PyTorch wheel for CPU or MPS. If you plan to run stem separation locally, follow Demucs and PyTorch install instructions for your platform.

Quick start (macOS / Linux)
---------------------------

1. Clone the repository:

```bash
git clone https://github.com/your/repo.git
cd repo
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

3. Install Python dependencies:

```bash
pip install -r requirements.txt
```

4. Install system dependencies (macOS example):

```bash
# install ffmpeg
brew install ffmpeg

# optional: follow Demucs installation docs; you can install the demucs pip package
pip install demucs
```

5. Start the API:

```bash
python app.py
```

By default the Flask app in this repository runs with `app.run(..., port=5002)`; the server will listen on port `5002` when started this way.

Configuration
-------------

Basic runtime settings are in `config.py`:

- `UPLOAD_FOLDER` — where uploaded files are saved (default: `static/uploads`)
- `CONVERTED_FOLDER` — where converted or generated files are stored (default: `static/converted`)
- `SESSION_TIMEOUT` — session timeout value used by the original app (may be unused in the stripped API)

You can edit `config.py` to change these directories, or override settings on application startup by modifying `app.config`.

Running the API
---------------

Start the app as shown in Quick start. Once running, the following endpoints are available (all under the `/audio` blueprint):

- `GET /audio/test` — simple health endpoint for the blueprint
- `POST /audio/analyze` — analyze an uploaded audio file
- `POST /audio/convert` — convert an uploaded audio file to a target format
- `POST /audio/separate` — perform stem separation on an uploaded audio file

There is also a general health endpoint at `/api/health` which returns diagnostics about external tools.

API: endpoints and examples
--------------------------

All `POST` endpoints accept multipart form uploads. Below are cURL examples.

1) Analyze audio (tempo and key)

```bash
curl -X POST "http://localhost:5002/audio/analyze" \
  -F "file=@/path/to/audio.mp3"
```

Successful response (JSON):

```json
{ "success": true, "analysis": { "success": true, "tempo": 120, "key": "Em" } }
```

2) Convert audio (format conversion)

```bash
curl -X POST "http://localhost:5002/audio/convert" \
  -F "file=@/path/to/audio.wav" \
  -F "format=mp3"
```

The endpoint returns the converted file as a download (`Content-Disposition: attachment`).

3) Separate stems (Demucs)

```bash
curl -X POST "http://localhost:5002/audio/separate" \
  -F "file=@/path/to/song.mp3" \
  -F "model=htdemucs"   # optional — defaults to htdemucs
```

This endpoint runs stem separation and returns a ZIP file containing stems (if the `separate_audio` helper is used). Stem separation may be slow (minutes) depending on model and hardware.

File lifecycle and cleanup
--------------------------

Uploaded files are saved into the `UPLOAD_FOLDER` with UUID-prefixed names. Converted or generated files are saved under `CONVERTED_FOLDER`.

The code schedules cleanup of temporary files. Be aware that the current implementation schedules some files for deletion after a short delay; if you need to keep outputs, adjust the cleanup policy in `services.py` or `utils.py`.

Development notes and recommendations
-----------------------------------

- Consolidate conversion logic: There are two conversion helper implementations in the repository. One (`utils.convert_audio`) invokes FFmpeg via subprocess, and another wrapper exists in `services.py`. Consider unifying them into a single well-documented function.
- Use safe subprocess invocation: avoid `shell=True` and prefer argument lists with `subprocess.run([...], check=True)` to prevent shell injection and quoting issues.
- Demucs: choose either the CLI invocation or the Python API and standardize output directories and filenames for predictability.
- Add upload size limits: set `app.config['MAX_CONTENT_LENGTH']` to protect the server from very large uploads.
- For production: run behind a WSGI server (Gunicorn / uWSGI) and add HTTPS/authorization if the API will be publicly accessible.

Troubleshooting
---------------

- If `ffmpeg` is not found: install it system-wide (`brew install ffmpeg` on macOS).
- If `demucs` errors or model files are missing: install or download the required Demucs model weights per Demucs documentation.
- PyTorch installation: installing the correct `torch` wheel for your platform/GPU is critical. Refer to https://pytorch.org/get-started/locally/ for platform-specific instructions.

Security considerations
-----------------------

This project is a developer API and is intentionally minimal. Before exposing it publicly, consider:

- Authentication and authorization (API keys, OAuth, or JWT)
- Rate limiting to prevent abuse
- Strict upload size limits and timeouts
- Input validation — the code currently saves uploaded files and relies on `ALLOWED_AUDIO_EXTENSIONS` but more checks (MIME type, scanning) can help
- Error handling — do not expose stack traces in production responses; log them securely instead
- Run the app in a sandboxed environment or container if you process untrusted audio

Contributing
------------

Contributions are welcome. Suggested steps:

1. Fork the repository
2. Create a feature branch
3. Add tests and documentation for changes
4. Open a pull request with a clear description of your changes

License
-------

This repository is intended to be open source. Add a `LICENSE` file to declare a license (MIT, Apache-2.0, etc.). If you want this project to be MIT-licensed, create a `LICENSE` file containing the MIT license text.

Contact and further help
------------------------

If you run into problems, open an issue in the repository with details about your environment, the commands you ran, and the errors you saw. Include `python --version`, `pip freeze` output, and `ffmpeg -version` where relevant.

What I can do next
-------------------

- Make conversion subprocess invocation safer (remove `shell=True`) and unify conversion helpers.
- Add `MAX_CONTENT_LENGTH` and file-size validations to endpoints.
- Increase or make configurable the cleanup delay for converted files.

If you want me to implement any of the above changes now, tell me which one to start with.
