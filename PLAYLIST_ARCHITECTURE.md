# Playlist Feature - User Flow Diagram

## User Journey

```
┌─────────────────────────────────────────────────────────────┐
│                    NOBZ BEATS APP                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  User Visits    │
                    │  Showcase Page  │
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Clicks "+"      │
                    │ on a Track      │
                    └─────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
          ┌─────▼─────┐              ┌─────▼─────┐
          │ Logged In │              │   Guest   │
          └─────┬─────┘              └─────┬─────┘
                │                           │
                ▼                           ▼
    ┌───────────────────────┐   ┌────────────────────────┐
    │  Show Playlists       │   │  Show Temp Playlist    │
    │  - Select Playlist    │   │  Option + Login/Signup │
    │  - Create New         │   │  Prompts               │
    └───────┬───────────────┘   └────────┬───────────────┘
            │                             │
            ▼                             ▼
    ┌───────────────────────┐   ┌────────────────────────┐
    │  Track Added to       │   │  Track Added to        │
    │  Permanent Playlist   │   │  Session Playlist      │
    └───────────────────────┘   └────────────────────────┘
            │                             │
            ▼                             ▼
    ┌───────────────────────┐   ┌────────────────────────┐
    │  Access via           │   │  Access via            │
    │  "My Playlists"       │   │  "Temporary Playlist"  │
    │  - View/Edit/Delete   │   │  - Cleared on close    │
    └───────────────────────┘   └────────────────────────┘
```

## Database Schema

```
┌────────────────┐
│     USERS      │
├────────────────┤
│ id (PK)        │
│ username       │
│ password       │
│ is_admin       │
│ created_at     │
└────────┬───────┘
         │ 1
         │
         │ has many
         │
         ▼ N
┌────────────────┐
│   PLAYLISTS    │
├────────────────┤
│ id (PK)        │
│ name           │
│ description    │
│ user_id (FK)   │
│ created_at     │
│ updated_at     │
└────────┬───────┘
         │ N
         │
         │ contains (many-to-many)
         │
         ▼ N
┌─────────────────────┐        ┌────────────────┐
│  PLAYLIST_TRACKS    │◄───────┤    TRACKS      │
├─────────────────────┤        ├────────────────┤
│ playlist_id (FK,PK) │        │ id (PK)        │
│ track_id (FK,PK)    │        │ name           │
└─────────────────────┘        │ description    │
                               │ file           │
                               │ artwork        │
                               │ like_count     │
                               │ play_count     │
                               └────────────────┘
```

## Route Structure

```
/
├── /register              → User registration
├── /login                 → User login
├── /logout                → Logout
│
├── /showcase              → Browse tracks (with + button)
│
├── /playlists             → View all user playlists
│   ├── /create            → Create new playlist (POST)
│   ├── /{id}              → View specific playlist
│   │   ├── /add/{track}   → Add track to playlist (POST)
│   │   ├── /remove/{track}→ Remove track (POST)
│   │   ├── /delete        → Delete playlist (POST)
│   │   └── /update        → Update playlist info (POST)
│   └── /api/playlists     → Get user playlists (AJAX)
│
└── /temp-playlist         → Temporary playlist (guests)
    ├── /add/{track}       → Add to temp playlist (POST)
    ├── /remove/{track}    → Remove from temp (POST)
    └── /clear             → Clear temp playlist (POST)
```

## Frontend Components

```
showcase.html
└── Modal: "Add to Playlist"
    ├── Logged In Users:
    │   ├── List of Playlists (clickable)
    │   └── "Create New Playlist" button
    │       └── Quick create form
    │
    └── Guest Users:
        ├── "Add to Temporary Playlist" button
        └── Login/Signup links

playlists.html
├── Playlist Grid
│   └── Each Card:
│       ├── View button → playlist_view.html
│       ├── Edit button → Edit modal
│       └── Delete button → Confirmation
│
└── "Create Playlist" button → Create modal

playlist_view.html
└── Track Table
    ├── Play button (global player)
    └── Remove button (from playlist)

temp_playlist.html
└── Track Table
    ├── Play button (global player)
    ├── Remove button
    ├── Clear All button
    └── Signup prompts
```

## Session Management

```
Flask Session (for guests)
└── session['temp_playlist']
    └── [track_id_1, track_id_2, track_id_3, ...]
    
    ↓ (cleared on browser close)
    
    Empty session
```

## Authentication Flow

```
base.html Navigation
│
├── if current_user.is_authenticated:
│   ├── My Playlists
│   ├── Logout
│   └── (Admin Panel if is_admin)
│
└── else (guest):
    ├── Login
    ├── Sign Up
    └── Temporary Playlist
```

## AJAX Interactions

```javascript
// Add to playlist
fetch('/playlist/{id}/add/{track_id}', {method: 'POST'})
  → Success: Alert + close modal
  → Error: Show error message

// Add to temp playlist  
fetch('/temp-playlist/add/{track_id}', {method: 'POST'})
  → Success: Alert + close modal
  → Error: Show error message

// Get playlists (for modal)
fetch('/api/playlists')
  → Returns: {playlists: [{id, name, track_count}, ...]}
  → Populates modal list
```
