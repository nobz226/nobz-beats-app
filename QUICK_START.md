# Quick Start - Playlist Feature

## Get Started in 3 Steps

### 1️⃣ Setup Database
```bash
# If you have an existing database, back it up first
cp instance/app.db instance/app.db.backup

# Remove old database
rm instance/app.db

# Create new database with playlist tables
flask shell
```

In the Flask shell:
```python
from app import db
db.create_all()
exit()
```

### 2️⃣ Start the App
```bash
python audio_app.py
```

### 3️⃣ Try It Out!

**For Users (Permanent Playlists):**
1. Go to http://localhost:5002/register
2. Create an account (username + password)
3. Browse to "Beats and Remixes"
4. Click the **+** button on any track
5. Create a playlist or add to existing one
6. Access "My Playlists" from the menu

**For Guests (Temporary Playlists):**
1. Go to http://localhost:5002/showcase
2. Click the **+** button on any track
3. Add to temporary playlist
4. View from menu → "Temporary Playlist"
5. *Note: Cleared when browser closes*

## Key Routes

- `/register` - Create account
- `/login` - User login
- `/playlists` - View your playlists (requires login)
- `/temp-playlist` - Temporary playlist (guests)
- `/showcase` - Browse tracks (add to playlists here)

## Features

✅ Create unlimited playlists
✅ Add/remove tracks
✅ Edit playlist names/descriptions
✅ Delete playlists
✅ Play tracks directly from playlists
✅ Session-based temp playlists for guests
✅ Smart UI that adapts to login status

That's it! The feature is fully integrated and ready to use. 🎵
