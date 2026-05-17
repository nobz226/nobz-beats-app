# Audio Tools API — Comprehensive Codebase Analysis

## Executive Summary

**Audio Tools API** is a lightweight Flask-based REST API designed for audio processing. It provides three core audio processing capabilities through HTTP endpoints: **audio analysis** (tempo/key detection), **format conversion** (MP3/WAV/FLAC), and **stem separation** (instrument isolation via Demucs AI).

The codebase follows a **service-layer architecture** with clear separation of concerns: HTTP request handling (routes), business logic (services), and low-level utilities (file I/O, audio processing).

---

## Architecture Overview

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Flask Application (app.py)                   │
│  - Config initialization                                        │
│  - Blueprint registration                                       │
│  - Directory setup                                              │
│  - Expired file cleanup                                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┴────────────────────┐
         │                                    │
    ┌────▼────────────┐          ┌──────────▼──────────┐
    │  Routes Layer   │          │  Configuration      │
    │  routes/        │          │  config.py          │
    │  ├─ __init__.py │          │  ├─ Upload folders  │
    │  └─ audio.py    │          │  ├─ Max file size   │
    │                 │          │  └─ Expiry policy   │
    │  HTTP Endpoints │          │                     │
    │  ├─ /analyze    │          │  environment vars   │
    │  ├─ /convert    │          │  (SECRET_KEY, etc)  │
    │  ├─ /separate   │          │                     │
    │  └─ /transcribe │          │                     │
    └────────┬────────┘          └─────────────────────┘
             │
    ┌────────▼──────────────────┐
    │   Services Layer          │
    │   services.py             │
    ├─ AudioAnalysisService     │
    ├─ AudioConversionService   │
    ├─ StemSeparationService    │
    ├─ AudioTranscriptionService│
    └────────┬──────────────────┘
             │
    ┌────────▼──────────────────┐
    │   Utilities Layer         │
    │   utils.py                │
    ├─ File I/O operations      │
    ├─ Audio analysis (librosa) │
    ├─ FFmpeg conversion        │
    ├─ Demucs integration       │
    └─ System health checks     │
             │
    ┌────────▼──────────────────┐
    │  External Dependencies    │
    ├─ librosa (audio analysis) │
    ├─ FFmpeg (conversion)      │
    ├─ Demucs (stem separation) │
    ├─ music21 (notation)       │
    └─ PyTorch (ML backend)     │
    └──────────────────────────┘
```

---

## Project Structure

```
audio-tools-API/
├── app.py                          # Main Flask app (production entry point)
├── audio_app.py                    # Alternative entry point (similar to app.py)
├── config.py                       # Configuration management
├── services.py                     # Service layer (business logic)
├── utils.py                        # Utility functions (file I/O, analysis, conversion)
│
├── routes/
│   ├── __init__.py                 # Blueprint registration system
│   └── audio.py                    # HTTP endpoints for audio operations
│
├── static/
│   ├── uploads/                    # Temporary uploaded audio files
│   ├── converted/                  # Processed/converted output files
│   ├── js/
│   │   └── tools.js                # Frontend JavaScript
│   ├── fonts/                      # Custom web fonts
│   └── favicon/                    # Favicon assets
│
├── templates/
│   ├── index.html                  # Landing page
│   └── tools.html                  # Interactive UI for testing endpoints
│
├── tests/
│   ├── conftest.py                 # Pytest configuration
│   ├── test_api_convert.py         # API endpoint tests
│   ├── test_services_audio_tools.py# Service layer tests
│   └── test_utils_convert.py       # Utility function tests
│
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables (not in repo)
├── .gitignore                      # Git ignore rules
├── README.md                       # Quick start guide
├── PROJECT_DESCRIPTION.md          # Detailed project description
└── LICENSE.md                      # MIT license
```

---

## Core Components

### 1. Configuration Layer (`config.py`)

**Purpose:** Centralized runtime configuration management

**Key Components:**
- `Config` — Base configuration class
  - `UPLOAD_FOLDER` — Temporary upload directory (`static/uploads`)
  - `CONVERTED_FOLDER` — Output directory for processed files (`static/converted`)
  - `MAX_CONTENT_LENGTH` — Maximum upload size (default: 100 MB)
  - `FILE_EXPIRY_SECONDS` — How long to keep processed files (default: 15 minutes)
  - `SESSION_TIMEOUT` — Session timeout (5 minutes)
  - `SECRET_KEY` — Flask session secret key

- `DevelopmentConfig` — Development overrides (DEBUG=True)
- `ProductionConfig` — Production overrides (DEBUG=False, stronger secret)

**Environment Variables:**
```bash
SECRET_KEY=<flask-session-secret>
MAX_CONTENT_LENGTH=104857600  # 100 MB in bytes
FILE_EXPIRY_SECONDS=900       # 15 minutes
```

**File Structure Creation:**
```python
@staticmethod
def init_app(app):
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(Config.CONVERTED_FOLDER, exist_ok=True)
```

---

### 2. Routes Layer (`routes/`)

#### 2.1 Blueprint Registration (`routes/__init__.py`)

```python
from routes.audio import audio_bp

all_blueprints = [audio_bp]

def register_blueprints(app):
    """Register all blueprints with Flask app"""
    for blueprint in all_blueprints:
        app.register_blueprint(blueprint)
```

**Pattern:** Centralizes blueprint registration for easy scaling

---

#### 2.2 Audio Endpoints (`routes/audio.py`)

All endpoints are under `/api` prefix and return JSON responses.

**Helper Functions:**
- `_get_extension(filename)` — Extract file extension
- `_is_valid_audio_file(file_obj)` — Validate audio file type
- `_error_response(message, status_code)` — Standardized error responses
- `_status_code_for_error(error_text)` — Map error types to HTTP status codes

**Endpoint: POST `/api/analyze`**
- **Purpose:** Detect tempo (BPM) and musical key
- **Request:** Multipart form with `file` field
- **Response:** JSON with `{success, analysis: {tempo, key}}`
- **Error Handling:** Returns 400 for invalid files, 413 for oversized files

**Endpoint: POST `/api/convert`**
- **Purpose:** Convert audio format
- **Request:** Multipart form with `file` and `format` fields (mp3/wav/flac)
- **Response:** Binary file download with attachment header
- **Service Used:** `AudioConversionService`

**Endpoint: POST `/api/separate`**
- **Purpose:** Separate audio stems (vocals, drums, bass, melody)
- **Request:** Multipart form with `file` and optional `model` fields
- **Response:** ZIP file containing separated stems
- **Service Used:** `StemSeparationService`

**Endpoint: POST `/api/transcribe`**
- **Purpose:** Transcribe monophonic audio to musical notes
- **Request:** Multipart form with `file` field
- **Response:** JSON with note events, BPM, and optional MusicXML
- **Service Used:** `AudioTranscriptionService`
- **Output Formats:** JSON (default) or MusicXML (with `format=xml` param)

**Endpoint: GET `/api/test`**
- **Purpose:** Health check for blueprint
- **Response:** `{success: true, message: "Audio blueprint is active"}`

---

### 3. Services Layer (`services.py`)

**Purpose:** Orchestrate business logic for audio operations

**Key Pattern:** Each service handles one domain (analysis, conversion, separation, transcription)

#### 3.1 AudioAnalysisService

```python
class AudioAnalysisService:
    def __init__(self, upload_folder, converted_folder)
    def analyze_file(self, audio_file) -> dict
```

**Workflow:**
1. Validate file upload
2. Save uploaded file with UUID filename
3. Call `analyze_audio_file()` from utils
4. Clean up temporary input file
5. Return analysis results (tempo, key)

**Error Handling:** Returns `{success: False, error: str}` on failure

---

#### 3.2 AudioConversionService

```python
class AudioConversionService:
    def __init__(self, upload_folder, converted_folder)
    def convert_file(self, audio_file, target_format) -> dict
```

**Workflow:**
1. Validate format (mp3/wav/flac)
2. Save uploaded file
3. Generate UUID-based output filename
4. Call `convert_audio()` from utils (uses FFmpeg)
5. Schedule file cleanup (threaded, configurable delay)
6. Return output file path

**Key Feature:** Asynchronous cleanup thread
```python
def _schedule_file_cleanup(self, file_path, delay_seconds):
    def delete_file():
        time.sleep(delay_seconds)
        cleanup_file(file_path)
    
    cleanup_thread = threading.Thread(target=delete_file, daemon=True)
    cleanup_thread.start()
```

---

#### 3.3 StemSeparationService

```python
class StemSeparationService:
    def __init__(self, upload_folder, converted_folder)
    def separate_stems(self, audio_file, model='htdemucs') -> dict
```

**Workflow:**
1. Validate file
2. Save uploaded file
3. Create output directory with UUID
4. Call `separate_audio()` to run Demucs
5. Compress stems into ZIP
6. Schedule directory cleanup
7. Return ZIP file path

**Supported Model:** `htdemucs` (6-stem separation)

---

#### 3.4 AudioTranscriptionService

```python
class AudioTranscriptionService:
    def __init__(self, upload_folder, converted_folder)
    def transcribe_file(self, audio_file) -> dict
```

**Workflow:**
1. Save uploaded file
2. Call `transcribe_audio_file()` from utils
3. Generate MusicXML from note events
4. Return notes, BPM, and MusicXML

---

### 4. Utilities Layer (`utils.py`)

**Purpose:** Low-level implementations of audio processing, file I/O, and system checks

#### 4.1 File Management Functions

**`save_uploaded_file(file_obj, upload_folder, original_filename=None) -> (uuid, file_path)`**
- Validates file extension against `ALLOWED_AUDIO_EXTENSIONS`
- Generates UUID-based filename for collision prevention
- Returns tuple: `(uuid, full_file_path)`

**Supported Audio Extensions:**
```python
ALLOWED_AUDIO_EXTENSIONS = {'.mp3', '.wav', '.flac', '.m4a', '.aif', '.aiff', '.ogg', '.aac'}
```

**`cleanup_file(file_path) -> bool`**
- Safely removes files or directories
- Handles both file and directory cleanup
- Uses `shutil.rmtree()` for directories
- Returns success status

**`cleanup_expired_files(directory_path, expire_seconds) -> list`**
- Scans directory for files older than `expire_seconds`
- Returns list of removed paths
- Called on app startup for directory cleanup

---

#### 4.2 Audio Analysis Functions

**`analyze_audio_file(file_path) -> dict`**

**Tempo Detection Algorithm:**
1. Load audio at 22,050 Hz (mono) using librosa
2. Calculate onset strength envelope
3. Try multiple starting BPMs: [60, 90, 120, 140, 180]
4. Collect tempo estimates from all starts
5. Group similar tempos (within 3 BPM)
6. Consider harmonic relationships (octaves)
7. Return highest-scoring tempo

**Key Detection Algorithm:** Krumhansl-Schmuckler
1. Extract chroma features from audio
2. Compare against major/minor key profiles
3. Try all 12 major keys + 12 minor keys (24 total)
4. Compute correlation for each key shift
5. Return key with highest correlation

**Return Format:**
```json
{
  "success": true,
  "tempo": 120,
  "key": "Em"
}
```

**Memory Management:**
- Loads audio at 22,050 Hz (low sample rate)
- Explicitly deletes intermediate arrays
- Calls `gc.collect()` after large operations

---

#### 4.3 Audio Conversion Function

**`convert_audio(input_path, output_path, output_format) -> bool`**

Uses FFmpeg with format-specific encoders:

**MP3 Encoding:**
```bash
ffmpeg -i input -codec:a libmp3lame -qscale:a 2 -y output.mp3
```
- Quality scale 2 (high quality)

**WAV Encoding:**
```bash
ffmpeg -i input -codec:a pcm_s16le -y output.wav
```
- 16-bit PCM

**FLAC Encoding:**
```bash
ffmpeg -i input -codec:a flac -y output.flac
```
- Lossless compression

**Process Execution:**
```python
proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
```
- Runs subprocess safely without `shell=True`
- Captures stdout/stderr
- Returns bool based on exit code

---

#### 4.4 Transcription Functions

**`transcribe_audio_file(file_path, hop_length=512, fmin='C2', fmax='C7') -> dict`**

**Pitch Detection Algorithm:**
1. Load audio at 22,050 Hz (mono)
2. Try librosa's `pyin` (preferred)
3. Fallback to `piptrack` if pyin fails
4. Convert Hz to MIDI to note names
5. Merge adjacent notes with gap tolerance
6. Clean and snap notes to beat grid
7. Estimate tempo

**Pitch Detection Range:** C2 (65.4 Hz) to C7 (2093 Hz)

**Note Merging Logic:**
- Groups consecutive frames with same pitch
- Merges notes separated by gaps ≤ 0.1 seconds
- Filters low-confidence notes

**Return Format:**
```json
{
  "success": true,
  "notes": [
    {"pitch": "C4", "start": 0.0, "duration": 0.5, "confidence": 0.9},
    {"pitch": "D4", "start": 0.5, "duration": 0.5, "confidence": 0.85}
  ],
  "bpm": 120
}
```

---

#### 4.5 MusicXML Conversion

**`notes_to_musicxml(notes, bpm=120, time_signature='4/4') -> str`**

Uses `music21` library to convert note events to MusicXML:

**Process:**
1. Clean and filter notes
2. Create music21 score/part
3. Add metadata (tempo, time signature, key, clef)
4. Insert notes with quantized durations
5. Generate measures
6. Export to XML string

**Error Handling:**
- Falls back to minimal empty score if export fails
- Handles invalid MIDI notes gracefully

---

#### 4.6 Stem Separation Integration

**`separate_audio(input_path, output_dir, model='htdemucs') -> str`**

Wrapper around Demucs CLI:

**Command Structure:**
```bash
demucs -n htdemucs -o output_dir --segment 7 --overlap 0.1 input_path
```

**Parameters:**
- `-n htdemucs` — Use htdemucs model (6 stems)
- `--segment 7` — Process in 7-second segments (memory optimization)
- `--overlap 0.1` — 10% overlap between segments

**Output Structure:**
```
output_dir/
├── htdemucs/
│   └── input_filename/
│       ├── drums.wav
│       ├── bass.wav
│       ├── other.wav (renamed to "melody")
│       ├── vocals.wav
│       └── [optional other stems]
└── stems.zip  (created by API)
```

**Returns:** Path to `stems.zip` containing all stems

---

#### 4.7 System Health Checks

**`check_system_tools() -> dict`**

Verifies availability of external tools:

```json
{
  "demucs_installed": true,
  "demucs_path": "/usr/local/bin/demucs",
  "ffmpeg_installed": true,
  "ffmpeg_path": "/usr/local/bin/ffmpeg",
  "torch_cache_exists": true,
  "torch_cache_nonempty": true,
  "torch_cache_files": ["pytorch_model_1", "pytorch_model_2"]
}
```

**Checks:**
- FFmpeg availability via `shutil.which()`
- Demucs availability
- PyTorch cache directory (`~/.cache/torch/hub/checkpoints`)

---

### 5. Main Application (`app.py` and `audio_app.py`)

#### 5.1 Initialization Sequence

```python
app = Flask(__name__)

# Load config
app_config = config['default']  # or config['development']
app.config.from_object(app_config)
app_config.init_app(app)

# Set upload limits
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB

# Create directories
ensure_directory_exists(app.config['UPLOAD_FOLDER'])
ensure_directory_exists(app.config['CONVERTED_FOLDER'])

# Cleanup expired files
cleanup_expired_files(app.config['CONVERTED_FOLDER'], app.config['FILE_EXPIRY_SECONDS'])

# Register routes
register_blueprints(app)
```

#### 5.2 Provided Routes

**GET `/` (index)**
- Landing page with documentation and usage examples
- Template: `templates/index.html`

**GET `/tools`**
- Interactive UI for testing endpoints
- Template: `templates/tools.html`

**GET `/api/health`**
- System health check
- Response: JSON from `check_system_tools()`

**GET `/api/test`**
- Audio blueprint health check

#### 5.3 Application Entry Points

**Production (`audio_app.py`):**
```python
if __name__ == '__main__':
    app.run(debug=True, port=5002)
```

**Development (`app.py`):**
```python
if __name__ == '__main__':
    app.run(debug=True, port=5002)
```

Both run on **port 5002** (not standard 5000)

---

## Data Flow Examples

### Example 1: Audio Analysis Flow

```
1. Client: POST /api/analyze
   └─ Multipart form with file

2. routes/audio.py:analyze_endpoint()
   ├─ Validate file present and is audio
   ├─ Check file size < MAX_CONTENT_LENGTH
   └─ Create AudioAnalysisService

3. services.py:AudioAnalysisService.analyze_file()
   ├─ save_uploaded_file() → utils
   ├─ analyze_audio_file() → utils
   └─ cleanup_file() → utils

4. utils.py:analyze_audio_file()
   ├─ Load audio at 22050 Hz (mono)
   ├─ Detect tempo (multi-pass BPM detection)
   ├─ Detect key (Krumhansl-Schmuckler)
   ├─ Cleanup memory (gc.collect())
   └─ Return {success, tempo, key}

5. routes/audio.py returns JSON response
   └─ Client: {success: true, analysis: {tempo: 120, key: "Em"}}
```

---

### Example 2: Format Conversion Flow

```
1. Client: POST /api/convert
   └─ Multipart form with file + format="mp3"

2. routes/audio.py:convert_endpoint()
   ├─ Validate format in ['mp3', 'wav', 'flac']
   └─ Create AudioConversionService

3. services.py:AudioConversionService.convert_file()
   ├─ Generate UUID output filename
   ├─ Call convert_audio() → utils
   ├─ Schedule cleanup thread (900 seconds delay)
   └─ Return output_path

4. utils.py:convert_audio()
   ├─ Build FFmpeg command (format-specific encoder)
   ├─ subprocess.run(cmd)
   ├─ Verify output file exists
   └─ Return bool

5. routes/audio.py:convert_endpoint()
   ├─ send_file(output_path, as_attachment=True)
   └─ Client receives binary file download

6. [Background] 900 seconds later:
   └─ Cleanup thread deletes output file
```

---

### Example 3: Stem Separation Flow

```
1. Client: POST /api/separate
   └─ Multipart form with file

2. routes/audio.py:separate_endpoint()
   └─ Create StemSeparationService

3. services.py:StemSeparationService.separate_stems()
   ├─ Create UUID output directory
   ├─ Call separate_audio() → services.py
   ├─ Schedule cleanup thread
   └─ Return zip_path

4. services.py:separate_audio()
   ├─ Build demucs command
   ├─ subprocess.Popen() with streaming output
   ├─ Parse progress from stdout
   ├─ Wait for process completion
   ├─ Create stems.zip from output directory
   └─ Return zip_path

5. routes/audio.py:separate_endpoint()
   ├─ send_file(zip_path, as_attachment=True)
   └─ Client receives ZIP download

6. [Background] 900 seconds later:
   └─ Cleanup thread removes directory + ZIP
```

---

## Dependencies & External Tools

### Python Packages

**Core Framework:**
- `Flask==3.1.0` — Web framework

**Audio Processing:**
- `librosa==0.10.2.post1` — Audio analysis (tempo, key, STFT, CQT)
- `soundfile==0.12.1` — Audio file I/O
- `numpy` — Numerical computations
- `demucs==4.0.1` — Stem separation AI model
- `torch==2.5.1` — PyTorch (ML backend for Demucs)
- `torchaudio==2.5.1` — Audio processing for PyTorch
- `music21==8.3.0` — Music notation (MusicXML generation)

**Testing:**
- `pytest` — Test framework

### System Dependencies

- **FFmpeg** — Audio format conversion
  - Install: `brew install ffmpeg` (macOS)
  - Used via subprocess for format conversion

- **Demucs CLI** — Stem separation
  - Installed via `pip install demucs`
  - Model files downloaded on first use

---

## Error Handling Patterns

### HTTP Status Codes

| Code | Scenario | Example |
|------|----------|---------|
| 200  | Success | File converted, JSON returned |
| 400  | Bad request | Invalid format, missing file, unsupported extension |
| 413  | Payload too large | File exceeds `MAX_CONTENT_LENGTH` |
| 500  | Server error | FFmpeg crash, out of memory |

### Service Layer Error Responses

All services return consistent error format:
```json
{
  "success": false,
  "error": "Descriptive error message"
}
```

**Validation Flow:**
1. File presence check
2. Audio file extension validation
3. File size check
4. Processing try/catch
5. Cleanup in finally block

---

## File Lifecycle & Cleanup

### Upload Files
- **Location:** `static/uploads/`
- **Naming:** `{uuid}_{original_filename}` (prevents collisions)
- **Lifetime:** Deleted after service completes (in finally block)
- **Trigger:** Immediate cleanup after processing

### Converted/Output Files
- **Location:** `static/converted/`
- **Naming:** `{uuid}_{original_filename}.{format}`
- **Lifetime:** 15 minutes (configurable via `FILE_EXPIRY_SECONDS`)
- **Cleanup:** Background thread scheduled per conversion

### Directory Cleanup
- **Function:** `cleanup_expired_files()` called on app startup
- **Scans:** `static/converted/` directory
- **Removes:** Any files/directories older than expiry time

### Session-Based Cleanup
```python
# Called on app startup
cleanup_expired_files(app.config['CONVERTED_FOLDER'], app.config['FILE_EXPIRY_SECONDS'])
```

---

## Configuration & Environment

### `.env` File (Not in Repo)
```bash
SECRET_KEY=your-secret-key-here
MAX_CONTENT_LENGTH=104857600       # 100 MB
FILE_EXPIRY_SECONDS=900            # 15 minutes
```

### Configuration Access in Code
```python
# In routes
max_size = current_app.config.get('MAX_CONTENT_LENGTH')
upload_folder = current_app.config['UPLOAD_FOLDER']

# Services receive config values
service = AudioConversionService(
    current_app.config['UPLOAD_FOLDER'],
    current_app.config['CONVERTED_FOLDER']
)
```

---

## Testing Strategy

### Test Files

**`test_api_convert.py`**
- Tests HTTP endpoints via Flask test client
- Mocks file upload and FFmpeg conversion
- Validates response headers and status codes

**`test_services_audio_tools.py`**
- Tests service layer logic
- Uses temporary directories (pytest fixtures)
- Mocks utility functions to isolate service behavior
- Validates service return format

**`test_utils_convert.py`**
- Tests utility layer functions
- Tests file I/O operations
- Tests audio conversion logic

### Test Patterns

**Fixture Pattern:**
```python
@pytest.fixture
def tmp_path(tmp_path):
    upload_dir = tmp_path / 'uploads'
    converted_dir = tmp_path / 'converted'
    yield (upload_dir, converted_dir)
```

**Mock Pattern:**
```python
monkeypatch.setattr(services, 'analyze_audio_file', lambda path: {'success': True, ...})
```

**Cleanup Verification:**
```python
assert len(list(upload_dir.iterdir())) == 0  # Upload file deleted
```

---

## Key Design Patterns

### 1. Service Layer Pattern
- Routes delegate to service classes
- Services orchestrate business logic
- Utilities handle low-level operations
- Clear separation of concerns

### 2. UUID-Based Filenames
```python
file_uuid = str(uuid.uuid4())
unique_filename = f"{file_uuid}_{original_filename}"
```
**Benefits:**
- Prevents filename collisions
- Enables per-file tracking
- Maintains original filename for user context

### 3. Cleanup Thread Pattern
```python
def _schedule_file_cleanup(self, file_path, delay_seconds):
    def delete_file():
        time.sleep(delay_seconds)
        cleanup_file(file_path)
    
    cleanup_thread = threading.Thread(target=delete_file, daemon=True)
    cleanup_thread.start()
```
**Benefits:**
- Asynchronous cleanup doesn't block response
- Configurable expiry delay
- Daemon thread allows app shutdown

### 4. Error Handling with Cleanup
```python
try:
    # Process file
    result = service.process(file)
finally:
    # Always cleanup
    if input_path and os.path.exists(input_path):
        cleanup_file(input_path)
```
**Benefits:**
- Guarantees cleanup even on error
- Prevents file accumulation
- Reduces disk usage

### 5. Subprocess Safe Execution
```python
# NO shell=True (security risk)
cmd = ['ffmpeg', '-i', input_path, '-codec:a', 'libmp3lame', output_path]
proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
```
**Benefits:**
- Prevents shell injection
- Proper argument escaping
- Clear error reporting

---

## Performance Considerations

### Memory Management
- **Audio Loading:** Always use `sr=22050, mono=True` to limit memory
- **Explicit Cleanup:** `del audio_array; gc.collect()`
- **Streaming Demucs:** Progressive output parsing instead of buffering entire output

### CPU Optimization
- **Demucs Segmentation:** `--segment 7` splits processing into 7-second chunks
- **Overlap:** `--overlap 0.1` reduces artifacts at boundaries
- **Hardware Acceleration:** PyTorch defaults to available hardware (MPS on Apple Silicon, CUDA on NVIDIA)

### Network Optimization
- **Streaming Downloads:** `send_file()` streams responses
- **Multipart Validation:** Early rejection of invalid files
- **Size Limits:** Configurable `MAX_CONTENT_LENGTH`

---

## Security Considerations

### Input Validation
- File extension whitelist
- File size limits
- MIME type validation (implicit via librosa)

### File Operations
- `subprocess.run()` without `shell=True`
- `secure_filename()` for user-provided names
- UUID-based internal naming

### Temporary Files
- Explicit cleanup after processing
- Automatic expiry of old files
- No file persistence beyond session

---

## Common Gotchas & Troubleshooting

### 1. Demucs Model Not Found
**Error:** `FileNotFoundError` when running Demucs
**Cause:** Models not downloaded
**Solution:** Run `demucs --help` to auto-download models

### 2. FFmpeg Not in PATH
**Error:** `FFmpeg executable not found`
**Cause:** FFmpeg not installed or not in system PATH
**Solution:** `brew install ffmpeg` (macOS) or verify PATH

### 3. Out of Memory with Large Files
**Error:** MemoryError during analysis
**Cause:** Audio loaded at full sample rate
**Solution:** Code already uses `sr=22050` (handles most cases)

### 4. Port Already in Use
**Error:** `Address already in use`
**Cause:** App running on port 5002 twice
**Solution:** Kill existing process: `lsof -i :5002 | kill -9`

### 5. CORS Issues (Frontend Testing)
**Error:** `Cross-Origin Request Blocked`
**Cause:** API and frontend on different origins
**Solution:** Install `flask-cors` and configure CORS headers

---

## Summary Table

| Component | Purpose | Key Technologies |
|-----------|---------|-------------------|
| `config.py` | Configuration management | Python config classes |
| `routes/audio.py` | HTTP endpoints | Flask blueprints |
| `services.py` | Business logic orchestration | Service classes, threading |
| `utils.py` | Low-level audio processing | librosa, subprocess, music21 |
| `app.py` | Application bootstrap | Flask app factory |
| **External** | Stem separation | Demucs, PyTorch |
| **External** | Audio format conversion | FFmpeg |
| **External** | Audio analysis | librosa, numpy |

---

## Development Roadmap

**Potential Enhancements:**
1. Add batch processing endpoint
2. Implement WebSocket for real-time progress
3. Add Redis caching for analysis results
4. Support for more Demucs models (5-stem, 4-stem)
5. Implement OAuth2 authentication
6. Add API rate limiting
7. Support for cloud storage (S3, GCS)
8. Containerization (Docker) for deployment

---

## Conclusion

The **Audio Tools API** is a well-structured, modular audio processing service built on Flask. It demonstrates clean architecture principles with clear separation of concerns, proper error handling, and efficient resource management. The codebase is maintainable, testable, and ready for production deployment with appropriate security hardening.
