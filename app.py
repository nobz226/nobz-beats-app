from flask import Flask, jsonify, render_template
import os
from config import config
from utils import ensure_directory_exists
from routes import register_blueprints

# Minimal Flask app focused on audio tools: analyzer, converter, separator

# Authentication decorators removed (project is audio-only)

# Environment, DB, and auth removed for stripped-down project
app = Flask(__name__)

# Load configuration (default)
app_config = config['default']
app.config.from_object(app_config)
app_config.init_app(app)

ensure_directory_exists(app.config['UPLOAD_FOLDER'])
ensure_directory_exists(app.config['CONVERTED_FOLDER'])


# Routes


# session cleanup removed - sessions and session-based cleanup are not used in this audio-only project
# guides route removed - documentation/chat UI removed

# chat API removed - AI chat integration stripped out
    
# chat removed - AI integration stripped

# index removed - home UI removed (audio API only)

# about route removed - UI removed

# showcase removed - UI removed

# Admin routes removed - project only exposes audio endpoints
# (admin dashboard, user accounts and playlist features have been stripped)

# Admin panel removed. Admin functionality is intentionally stripped in this audio-only project.

# download_tracks removed - admin downloads are no longer part of the stripped project.

# delete_tracks removed - admin deletion is removed from the stripped project.

# logout removed - user account system stripped out

# remove_artwork removed - artwork management removed from stripped project.

# like_track removed - engagement features removed from stripped project.

# unlike_track removed - engagement features removed from stripped project.

# clear_likes removed - engagement features removed from stripped project.

# clear_unlikes removed - engagement features removed from stripped project.

# User registration removed - user accounts stripped from project.

# User login removed - no user login for stripped project.

# Playlist Routes

# Playlist routes removed - playlists are not part of the stripped project.

# create_playlist removed - playlists removed from project.

# view_playlist removed - playlists removed from project.

# add_to_playlist removed - playlist functionality removed.

# remove_from_playlist removed - playlist functionality removed.

# delete_playlist removed - playlist functionality removed.

# update_playlist removed - playlist functionality removed.

# get_user_playlists removed - playlists API removed.

# Session-based temporary playlists removed - stripped project

# Root landing page (simple static docs)
@app.route('/')
def index():
    return render_template('index.html')

# Interactive tools page (forms for analyze/convert/separate)
@app.route('/tools')
def tools():
    return render_template('tools.html')

# Health check API
@app.route('/api/health')
def api_health():
    from utils import check_system_tools
    return jsonify(check_system_tools())

# Register the audio blueprint (analyzer, converter, separator)
register_blueprints(app)

if __name__ == '__main__':
    app.run(debug=True, port=5002)