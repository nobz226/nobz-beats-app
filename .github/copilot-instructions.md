# NOBZ BEATS APP - AI Development Guide

## Architecture Overview

This is a **Flask-based music production web app** with audio processing capabilities. Key pattern: **Service Layer Architecture** separates business logic (audio processing) from route handlers.

- **Blueprint routing** for modular organization ([routes/audio.py](../routes/audio.py))
- **Service classes** handle heavy processing ([services.py](../services.py)): `AudioConversionService`, `StemSeparationService`
- **Utility layer** ([utils.py](../utils.py)) for file operations, audio analysis
- **SQLAlchemy ORM** with Flask-Login for auth ([models.py](../models.py))
- **User playlists** - Many-to-many relationship between Users, Playlists, and Tracks
- **Session-based temp playlists** - Non-authenticated users get temporary playlists via Flask sessions

## Critical Dependencies & Processing

### Audio Processing Pipeline
1. **Demucs (htdemucs model)** - Stem separation runs via `demucs.separate.main()` CLI wrapper
   - Outputs to `static/converted/htdemucs/<session_id>/` structure
   - Example: [services.py](../services.py#L157-L165) shows `demucs.separate.main(["-n", "htdemucs", ...])`

2. **Librosa** - Audio analysis (key/tempo detection)
   - Always load with `sr=22050, mono=True` to manage memory
   - See [utils.py](../utils.py#L68-L70) for proper loading pattern

3. **FFmpeg** - Format conversion (handled via subprocess in `utils.py`)
   - Must be installed and in system PATH

### File Lifecycle & Cleanup Pattern
**Critical**: All uploads use UUID-based filenames to prevent collisions and enable cleanup

```python
# Pattern used throughout codebase:
file_uuid, input_path = save_uploaded_file(audio_file, upload_folder)
# ... process ...
cleanup_file(input_path)  # Always cleanup in finally block
```

- Temporary files scheduled for deletion (e.g., 15s delay in [services.py](../services.py#L89))
- Session-based cleanup via `cleanup_session()` in [app.py](../app.py#L82-L103)

## Configuration & Environment

### Environment Variables (.env required)
```bash
TOGETHER_API_KEY=<together.ai key>  # For AI chatbot (LLaMA 3.3 70B)
ADMIN_USER=<username>
ADMIN_PASSWORD=<password>
SECRET_KEY=<flask secret>
```

### Config Pattern
- Uses config objects: `config['development']` vs `config['production']` ([config.py](../config.py))
- Directories auto-created via `Config.init_app()` 
- Upload folders: `static/uploads/`, `static/converted/`

## Development Workflows

### Running the App
```bash
# Setup (first time)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
# Create .env file with required variables

# Initialize DB (in flask shell)
flask shell
>>> from app import db
>>> db.create_all()
>>> exit()

# Run
python app.py  # Runs on http://localhost:5000
```

### Database Migrations
⚠️ No Alembic migrations currently - uses raw `db.create_all()`. To modify schema:
1. Update [models.py](../models.py)
2. Delete `instance/app.db`
3. Run `db.create_all()` in flask shell

### Playlist System
- **Authenticated users**: Permanent playlists stored in database (User → Playlist → Track many-to-many)
- **Guest users**: Temporary playlists stored in Flask session (cleared on browser close)
- **Pattern**: Check `current_user.is_authenticated` in templates to show appropriate UI
- **AJAX operations**: All playlist add/remove operations use fetch API for smooth UX

## Code Conventions

### Routing Pattern
- Blueprints registered via `register_blueprints(app)` in [routes/__init__.py](../routes/__init__.py)
- Route format: `/audio/<action>` for audio tools
- Main app routes in [app.py](../app.py) for core pages (home, showcase, admin)

### Error Handling & Logging
**Always** use print statements with `===` delimiters for debugging:
```python
print("=== FUNCTION_NAME CALLED ===")
print(f"Processing file: {filename}")
```
Pattern used throughout [services.py](../services.py), [utils.py](../utils.py), [routes/audio.py](../routes/audio.py)

### Memory Management
For audio processing, explicitly call `gc.collect()` after loading large files:
```python
del audio_file
import gc
gc.collect()
```
See [routes/audio.py](../routes/audio.py#L54-L56)

### Admin Protection
Use both decorators for admin routes:
```python
@login_required
@admin_required
def admin_panel():
    ...
```
Pattern defined in [app.py](../app.py#L62-L69)

## AI Integration (Together API)

LLaMA 3.3 70B chatbot on `/guides` endpoint with specialized system prompt:
- Friendly music production assistant persona ("Alex")
- Configured with temperature=0.7, top_p=0.7 ([app.py](../app.py#L123-L165))
- Streaming responses for real-time chat

## Common Gotchas

1. **URL generation in services**: Services can't use `url_for()` outside request context - hardcode paths like `/static/converted/{filename}` ([services.py](../services.py#L82))

2. **Demucs output structure**: Outputs nested as `converted/htdemucs/<session_id>/<stems>` - must navigate this hierarchy ([services.py](../services.py#L181-L194))

3. **File extension validation**: Use explicit allowed lists for security:
   ```python
   allowed_extensions = ['.mp3', '.wav', '.flac']
   ```

4. **Background processing**: Threading used for file cleanup, but main processing is synchronous (no Celery/Redis)

## Key Files Reference
- [app.py](../app.py) - Main Flask app, core routes, AI chatbot, playlist routes
- [services.py](../services.py) - Audio conversion & stem separation services
- [utils.py](../utils.py) - File handling, librosa analysis
- [routes/audio.py](../routes/audio.py) - Audio tool endpoints
- [models.py](../models.py) - User, Track & Playlist ORM models
- [config.py](../config.py) - Environment configs
- [forms.py](../forms.py) - WTForms for registration, playlists, and tracks
