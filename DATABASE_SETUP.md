# Database Setup Instructions

## Initial Setup (First Time)

If you're setting up the database for the first time:

```bash
flask shell
```

Then in the Flask shell:

```python
from app import db
db.create_all()
exit()
```

## Migrating Existing Database

If you already have a database and want to add the playlist feature:

**Option 1: Fresh Start (Recommended for Development)**
1. Backup your current database:
   ```bash
   cp instance/app.db instance/app.db.backup
   ```

2. Delete the current database:
   ```bash
   rm instance/app.db
   ```

3. Create new database with all tables:
   ```bash
   flask shell
   ```
   
   Then:
   ```python
   from app import db
   db.create_all()
   exit()
   ```

**Option 2: Manual Migration (Keep Existing Data)**

1. Open SQLite database:
   ```bash
   sqlite3 instance/app.db
   ```

2. Run these SQL commands:
   ```sql
   -- Add created_at to users table
   ALTER TABLE users ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;
   
   -- Create playlists table
   CREATE TABLE IF NOT EXISTS playlists (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       name VARCHAR(200) NOT NULL,
       description VARCHAR(500),
       user_id INTEGER NOT NULL,
       created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
       updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
       FOREIGN KEY (user_id) REFERENCES users(id)
   );
   
   -- Create playlist_tracks association table
   CREATE TABLE IF NOT EXISTS playlist_tracks (
       playlist_id INTEGER NOT NULL,
       track_id INTEGER NOT NULL,
       PRIMARY KEY (playlist_id, track_id),
       FOREIGN KEY (playlist_id) REFERENCES playlists(id),
       FOREIGN KEY (track_id) REFERENCES tracks(id)
   );
   
   .exit
   ```

## Testing the Setup

1. Start the application:
   ```bash
   python audio_app.py
   ```

2. Navigate to: `http://localhost:5002/register`

3. Create a test account

4. Try creating a playlist and adding tracks

## Features Added

- ✅ User registration and login
- ✅ Personal playlists (for logged-in users)
- ✅ Temporary playlists (for non-logged-in users)
- ✅ Add/remove tracks from playlists
- ✅ Create, edit, delete playlists
- ✅ View playlist details
