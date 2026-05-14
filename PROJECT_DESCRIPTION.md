# Audio Tools API — Project Description

## Overview

**Audio Tools API** is a lightweight, self-contained Flask-based REST API that exposes powerful audio processing tools. It provides three core capabilities that audio applications can integrate via HTTP endpoints:

1. **Audio Analysis** — Detect tempo (BPM) and musical key from audio files
2. **Format Conversion** — Convert between popular audio formats (MP3, WAV, FLAC)
3. **Stem Separation** — Isolate vocals, drums, bass, and other instruments using Demucs AI

The API is designed for **developer teams** building audio applications who want quick access to these features without implementing them from scratch. It's open-source (MIT License), self-hosted, and minimal—keeping dependencies and complexity low while maintaining practical functionality.

---

## Architecture & Project Structure

### Core Files

```
audio-tools-API/
├── app.py                 # Main Flask application entry point
├── config.py              # Configuration (folders, upload limits, timeouts)
├── requirements.txt       # Python dependencies
│
├── routes/
│   ├── __init__.py        # Blueprint registration system
│   └── audio.py           # HTTP endpoints (analyze, convert, separate)
│
├── services.py            # Service layer (business logic for conversions/separation)
├── utils.py               # Utility functions (file I/O, analysis, audio conversion, health checks)
│
├── static/
│   ├── uploads/           # Temporary uploaded files
│   ├── converted/         # Converted and processed audio outputs
│   ├── js/                # Frontend JavaScript
│   ├── fonts/             # Custom web fonts
│   └── favicon/           # Favicon assets
│
└── templates/
    ├── index.html         # Landing page with documentation
    └── tools.html         # Interactive UI for testing endpoints
```

### Separation of Concerns

| Component | Purpose | Key Responsibility |
|-----------|---------|-------------------|
| `app.py` | Application bootstrap | Initialize Flask, load config, register routes |
| `routes/audio.py` | HTTP request handling | Parse requests, validate inputs, return responses |
| `services.py` | Business logic | Orchestrate conversions, separation, call utils |
| `utils.py` | Low-level operations | File I/O, audio analysis, FFmpeg calls, health checks |
| `config.py` | Runtime settings | Define folders, upload limits, cleanup policies |

---

## API Endpoints

All endpoints are under the `/audio` prefix and accept multipart file uploads.

### 1. Audio Analysis
**Endpoint:** `POST /audio/analyze`

Analyzes an uploaded audio file to detect **tempo (BPM)** and **musical key**.

**Request:**
```bash
curl -X POST "http://localhost:5002/audio/analyze" \
  -F "file=@song.mp3"
```

**Response:**
```json
{
  "success": true,
  "analysis": {
    "success": true,
    "tempo": 120,
    "key": "Em"
  }
}
```

**How it works:**
- Loads audio at 22,050 Hz sample rate (mono) using `librosa`
- Computes onset strength envelope to find rhythmic patterns
- Runs tempo detection from multiple starting points (60, 90, 120, 140, 180 BPM)
- Groups similar tempos and considers harmonics (octaves) for accuracy
- Detects key using Krumhansl-Schmuckler algorithm with music theory profiles
- Returns the most confident key (e.g., "Em", "C", "F#m")

---

### 2. Format Conversion
**Endpoint:** `POST /audio/convert`

Converts an audio file to a target format (MP3, WAV, FLAC).

**Request:**
```bash
curl -X POST "http://localhost:5002/audio/convert" \
  -F "file=@song.wav" \
  -F "format=mp3"
```

**Response:** Binary file download with `Content-Disposition: attachment`

**How it works:**
- Validates target format (must be mp3, wav, or flac)
- Saves uploaded file with UUID prefix
- Calls `ffmpeg` subprocess to perform format conversion
- Returns converted file as a direct download
- Automatically schedules input file for cleanup after 15 minutes (configurable)

---

### 3. Stem Separation
**Endpoint:** `POST /audio/separate`

Performs AI-based stem separation to isolate vocals, drums, bass, and melody.

**Request:**
```bash
curl -X POST "http://localhost:5002/audio/separate" \
  -F "file=@song.mp3" \
  -F "model=htdemucs"  # optional, defaults to htdemucs
```

**Response:** ZIP file containing separated stems (drums.mp3, bass.mp3, vocals.mp3, other.mp3)

**How it works:**
- Saves uploaded file with UUID prefix
- Invokes Demucs CLI with specified model (htdemucs by default)
- Demucs uses PyTorch and deep learning to separate audio sources
- Converts separated stems to MP3 format
- Packages stems into a ZIP file for download
- **Note:** Stem separation is **resource-intensive** and may take several minutes depending on audio length and hardware

---

### 4. Health Check (System Diagnostics)
**Endpoint:** `GET /api/health`

Returns diagnostic information about external dependencies.

**Response:**
```json
{
  "demucs_installed": true,
  "demucs_path": "/usr/local/bin/demucs",
  "ffmpeg_installed": true,
  "ffmpeg_path": "/usr/local/bin/ffmpeg",
  "torch_cache_exists": true,
  "torch_cache_nonempty": true,
  "torch_cache_files": ["htdemucs.pt", ...]
}
```

---

### 5. Test Endpoint
**Endpoint:** `GET /audio/test`

Simple health check for the audio blueprint.

**Response:**
```json
{
  "success": true,
  "message": "Audio blueprint is active"
}
```

---

## Data Flow & Request Lifecycle

### Typical Request Flow

```
Client HTTP Request
    ↓
Flask Route Handler (routes/audio.py)
    ├── Validate input (file present, format valid)
    ├── Check upload size
    └── Save uploaded file with UUID prefix
    ↓
Service Layer (services.py)
    ├── Perform business logic
    │   (conversion, analysis, separation)
    ├── Call utility functions
    └── Return result dict
    ↓
Utility Functions (utils.py)
    ├── Call FFmpeg or librosa
    ├── Execute Demucs CLI
    └── Manage file I/O
    ↓
Response
    ├── JSON metadata (for analyze)
    ├── File download (for convert/separate)
    └── Error response on failure
    ↓
Cleanup Thread (scheduled in background)
    └── Delete input/output files after configurable delay
```

---

## File Lifecycle & Cleanup

### Upload Flow
1. Client uploads file → saved to `static/uploads/` with UUID prefix
2. File processed (analyzed, converted, or separated)
3. Output saved to `static/converted/`
4. Response sent to client (download link or metadata)

### Cleanup Policy
- **Uploaded files** — Deleted immediately after processing (in route handler's `finally` block)
- **Converted/output files** — Scheduled for deletion after `FILE_EXPIRY_SECONDS` (default: 15 minutes)
- **Cleanup mechanism** — Background daemon threads monitor and remove expired files

**Why?** Prevents disk space from filling up with temporary files over time.

---

## Configuration

Settings are managed in `config.py` and can be overridden with environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `UPLOAD_FOLDER` | `static/uploads` | Where uploaded files are stored |
| `CONVERTED_FOLDER` | `static/converted` | Where outputs are stored |
| `MAX_CONTENT_LENGTH` | 100 MB | Maximum upload size |
| `FILE_EXPIRY_SECONDS` | 900 (15 min) | How long to keep generated files |
| `SECRET_KEY` | `change-me` | Flask session key (change in production) |

**To override at startup:**
```bash
export MAX_CONTENT_LENGTH=524288000  # 500 MB
export FILE_EXPIRY_SECONDS=3600      # 1 hour
export SECRET_KEY="your-secure-key"
python app.py
```

---

## Dependencies

### Python Libraries
- **Flask** (3.1.0) — Web framework
- **librosa** (0.10.2) — Audio analysis (tempo, key detection)
- **demucs** (4.0.1) — Stem separation via CLI
- **torch** (2.5.1) — PyTorch (required by Demucs)
- **torchaudio** (2.5.1) — Audio processing for PyTorch
- **soundfile** (0.12.1) — Audio file I/O
- **pytest** — Testing framework

### System Dependencies
- **Python 3.8+**
- **FFmpeg** — Audio format conversion (install: `brew install ffmpeg` on macOS)
- **Demucs models** — Pre-trained weights (auto-downloaded on first use)

---

## How to Run

### Quick Start (Development)

```bash
# 1. Clone and setup
git clone <repo>
cd audio-tools-API
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install system tools
brew install ffmpeg  # macOS
# Linux: sudo apt-get install ffmpeg

# 4. Start the API
python app.py
```

The API will run on **http://localhost:5002** by default.

### Production Deployment

For production, use a WSGI server:

```bash
# Install Gunicorn
pip install gunicorn

# Run with multiple workers
gunicorn -w 4 -b 0.0.0.0:5002 app:app
```

---

## Key Features & Implementation Details

### 1. Advanced Tempo Detection
- **Multi-point onset analysis** — Tests multiple starting points (60, 90, 120, 140, 180 BPM)
- **Tempo clustering** — Groups similar tempos within ±3 BPM tolerance
- **Harmonic consideration** — Accounts for octave relationships (half/double tempos)
- **Frequency weighting** — Returns most common tempo across estimates

### 2. Music Theory-Based Key Detection
- **Chroma features** — Extracts pitch information from audio
- **Krumhansl-Schmuckler algorithm** — Correlates chroma against major/minor profiles
- **24 key search** — Tests all 12 major and 12 minor keys
- **Confidence scoring** — Returns highest-correlated key

### 3. Memory-Efficient Audio Processing
- **Low sample rate loading** — Loads audio at 22,050 Hz to reduce memory footprint
- **Selective reloading** — Reloads audio only for key detection (up to 30 sec duration)
- **Garbage collection** — Explicitly frees memory after large operations
- **CUDA cleanup** — Clears GPU cache if available

### 4. Safe File Handling
- **UUID prefixing** — Prevents filename collisions and security issues
- **Secure filename validation** — Sanitizes user-provided filenames
- **Extension whitelist** — Only allows known audio formats
- **Subprocess safety** — Uses argument lists instead of `shell=True` to prevent injection

### 5. Concurrent Request Support
- **Background cleanup threads** — File deletion doesn't block API responses
- **Service isolation** — Each service has own folder configuration
- **Daemon threads** — Cleanup threads are non-blocking and exit gracefully

---

## Testing

Unit tests are in the `tests/` directory:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api_convert.py -v

# Run with coverage
pytest --cov=. tests/
```

**Test structure:**
- `test_api_convert.py` — HTTP endpoint tests
- `test_utils_convert.py` — Utility function tests

---

## Security Considerations

### Current Implementation (Development-Focused)
- ✅ Input validation (extension whitelist, size limits)
- ✅ Safe subprocess invocation (no shell injection)
- ✅ File isolation (UUID prefixes, separate folders)
- ✅ Upload size limits (configurable)

### Production Recommendations
- 🔒 Add authentication (API keys, OAuth, JWT)
- 🔒 Implement rate limiting (prevent abuse)
- 🔒 Add timeout policies (prevent long-running tasks)
- 🔒 Validate MIME types (not just extensions)
- 🔒 Run in isolated container/sandbox
- 🔒 Use HTTPS/TLS
- 🔒 Don't expose stack traces (log securely instead)
- 🔒 Set strict resource quotas (memory, CPU, storage)

---

## Common Issues & Troubleshooting

| Problem | Solution |
|---------|----------|
| FFmpeg not found | Install: `brew install ffmpeg` (macOS) or `apt-get install ffmpeg` (Linux) |
| Demucs CLI not found | `pip install demucs` or add to PATH |
| PyTorch installation fails | Visit https://pytorch.org/get-started/locally/ for platform-specific wheel |
| Stem separation takes too long | Normal for long audio; adjust `--segment` in services.py to reduce quality |
| Out of memory errors | Reduce sample rate, lower MAX_CONTENT_LENGTH, or add swap space |
| Port 5002 already in use | Change port: `app.run(port=5003)` in app.py |

---

## Development Notes & Recommendations

### Code Quality Improvements
1. **Unify conversion logic** — Two conversion helpers exist; consolidate into single function
2. **Demucs integration** — Choose either CLI or Python API; standardize output paths
3. **Error responses** — Consider more granular error codes (not just success/error)
4. **Logging** — Replace print statements with proper logging framework

### Performance Optimizations
1. **Caching** — Cache model weights on first load
2. **Async processing** — Use Celery/Redis for long-running tasks (stem separation)
3. **Compression** — Return gzip-compressed responses for JSON
4. **Database** — Track processing jobs for status updates

### Feature Roadmap Ideas
- Batch processing (multiple files in one request)
- Job queuing system for stem separation
- Webhook callbacks for async completion
- Audio effect processing (EQ, compression, reverb)
- Metadata extraction (ID3 tags, audio duration, channels)
- Real-time WebSocket streaming

---

## License & Attribution

**MIT License** — Anyone may download, modify, and redistribute this code.

Copyright (c) 2026 Eduard Rotaru

See `LICENSE.md` for full license text.

---

## Getting Help

### Debugging
1. Check `/api/health` endpoint for system dependency status
2. Review console output (Flask debug server shows request logs)
3. Check `static/uploads/` and `static/converted/` for file artifacts
4. Enable pytest with verbose mode: `pytest -v`

### Common Questions
- **Q: Can I host this publicly?**
  - A: Yes, but add authentication and rate limiting first (see Security section)
  
- **Q: How large can files be?**
  - A: Default is 100 MB; adjust `MAX_CONTENT_LENGTH` config
  
- **Q: Does it work on Windows?**
  - A: Yes, but ensure FFmpeg and Python are in PATH; use `venv\Scripts\activate` instead
  
- **Q: Can I use GPU for stem separation?**
  - A: Yes, install GPU-enabled PyTorch; edit services.py to use `-d cuda`

### Reporting Issues
Open an issue on GitHub with:
- Environment: `python --version`, `pip freeze`, `ffmpeg -version`
- Error message and stack trace
- Steps to reproduce
- Example audio file (if possible)

---

## Summary

**Audio Tools API** provides a simple, focused REST API for audio processing. It's ideal for developers who want to integrate tempo detection, key detection, format conversion, and stem separation without building these features from scratch. The code is clean, well-documented, and production-ready with minor enhancements.

**Start here:** `python app.py` and visit http://localhost:5002/tools for an interactive demo.
