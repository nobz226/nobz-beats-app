from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from extensions import db
from models import Track, User
from forms import TrackForm
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from flask import send_from_directory, send_file
import subprocess
import uuid
from pathlib import Path
import threading
from threading import Timer
import time
import requests as http_requests
from dotenv import load_dotenv
from together import Together
import ssl
import shutil
import warnings
import traceback
from utils import ensure_directory_exists, save_uploaded_file, cleanup_file, analyze_audio_file, convert_audio
from services import AudioConversionService, StemSeparationService
from config import config
from routes import register_blueprints

warnings.filterwarnings("ignore")
ssl._create_default_https_context = ssl._create_unverified_context

# Load environment variables
load_dotenv()

# Initialize Together API client
client = Together(api_key=os.getenv('TOGETHER_API_KEY'))

# Create Flask app
app = Flask(__name__)

# Load configuration
app_config = config['development']  # Change to 'production' for production
app.config.from_object(app_config)
app_config.init_app(app)

# Initialize database
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin'

# Active conversion sessions storage
ACTIVE_SESSIONS = {}

# Register blueprints
register_blueprints(app)

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Admin access required.", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Routes


def cleanup_session(session_id):
    """Clean up session files and data"""
    try:
        print(f"=== CLEANUP_SESSION CALLED for session {session_id} ===")
        
        # Clean up session directory in converted folder
        session_dir = os.path.join(app.config['CONVERTED_FOLDER'], session_id)
        print(f"Checking if session directory exists: {session_dir}")
        if os.path.exists(session_dir):
            print(f"Removing session directory: {session_dir}")
            shutil.rmtree(session_dir)
            print(f"Successfully removed session directory: {session_dir}")
        
        # Clean up any files in the uploads folder
        uploads_dir = app.config['UPLOAD_FOLDER']
        print(f"Checking for files in uploads folder: {uploads_dir}")
        if os.path.exists(uploads_dir):
            for filename in os.listdir(uploads_dir):
                if session_id in filename:
                    file_path = os.path.join(uploads_dir, filename)
                    print(f"Removing upload file: {file_path}")
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                    print(f"Successfully removed: {file_path}")
        
        # Remove session from active sessions
        if session_id in ACTIVE_SESSIONS:
            print(f"Removing session from ACTIVE_SESSIONS: {session_id}")
            del ACTIVE_SESSIONS[session_id]
            print(f"Successfully removed session from ACTIVE_SESSIONS")
            
    except Exception as e:
        print(f"Error cleaning up session {session_id}: {str(e)}")
        import traceback
        traceback.print_exc()

@app.route('/guides')
def guides():
    latest_track = Track.query.order_by(Track.date_added.desc()).first()
    return render_template('guides.html', latest_track=latest_track)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '')
    
    try:
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Your name is Alex. You are a music production expert who helps people learn about music production, DAWs, mixing, and music theory, especially hip hop beatmaking. Try not to repeat yourself too much and be funny sometimes. Make the experience of learning music production and hip hop beats as fun as possible"
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            temperature=0.7,
            top_p=0.7,
            top_k=50,
            repetition_penalty=1
        )
        
        answer = response.choices[0].message.content
        return jsonify({"answer": answer})
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"answer": "Sorry, I encountered an error. Please try again."}), 500

@app.route('/')
def index():
    latest_track = Track.query.order_by(Track.date_added.desc()).first()
    return render_template('home.html', latest_track=latest_track)

@app.route('/about')
def about():
    latest_track = Track.query.order_by(Track.date_added.desc()).first()
    return render_template('about.html', latest_track=latest_track)

@app.route('/showcase')
def showcase():
    sort_by = request.args.get('sort', 'date_desc')
    
    if sort_by == 'name_asc':
        tracks = Track.query.order_by(Track.name.asc()).all()
    elif sort_by == 'name_desc':
        tracks = Track.query.order_by(Track.name.desc()).all()
    elif sort_by == 'date_asc':
        tracks = Track.query.order_by(Track.date_added.asc()).all()
    elif sort_by == 'play_count':
        tracks = Track.query.order_by(Track.play_count.desc()).all()
    elif sort_by == 'like_count':  # New sorting option
        tracks = Track.query.order_by(Track.like_count.desc()).all()
    else:  # date_desc is default
        tracks = Track.query.order_by(Track.date_added.desc()).all()
    
    latest_track = Track.query.order_by(Track.date_added.desc()).first()
    return render_template('showcase.html', tracks=tracks, sort_by=sort_by, latest_track=latest_track)

@app.route('/admin', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_panel'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, is_admin=True).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for('admin_panel'))
        else:
            flash("Invalid admin credentials.", "danger")

    latest_track = Track.query.order_by(Track.date_added.desc()).first()
    return render_template('login.html', latest_track=latest_track)

@app.route('/admin/panel', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_panel():
    tracks = Track.query.order_by(Track.date_added.desc()).all()
    latest_track = tracks[0] if tracks else None
    form = TrackForm()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add' and form.validate_on_submit():
            # Get the track name and create a safe filename
            track_name = form.name.data
            safe_name = secure_filename(track_name)
            
            new_track = Track(
                name=track_name,
                description=form.description.data or ""
            )

            # Handle audio file
            if 'file' in request.files and request.files['file']:
                music_file = request.files['file']
                file_ext = os.path.splitext(music_file.filename)[1]
                music_filename = safe_name + file_ext
                music_file.save(os.path.join(app.config['UPLOAD_FOLDER'], music_filename))
                new_track.file = music_filename

            # Handle primary artwork
            if 'artwork' in request.files and request.files['artwork']:
                artwork = request.files['artwork']
                art_ext = os.path.splitext(artwork.filename)[1]
                artwork_filename = safe_name + "_artwork" + art_ext
                artwork.save(os.path.join(app.config['UPLOAD_FOLDER'], artwork_filename))
                new_track.artwork = artwork_filename
            else:
                new_track.artwork = "No Artwork"

            # Handle secondary artwork
            if 'artwork_secondary' in request.files and request.files['artwork_secondary']:
                secondary = request.files['artwork_secondary']
                sec_ext = os.path.splitext(secondary.filename)[1]
                secondary_filename = safe_name + "_secondary" + sec_ext
                secondary.save(os.path.join(app.config['UPLOAD_FOLDER'], secondary_filename))
                new_track.artwork_secondary = secondary_filename
            else:
                new_track.artwork_secondary = "No Secondary Artwork"

            db.session.add(new_track)
            db.session.commit()
            flash('New track added successfully!', 'success')

        elif action == 'update':
            track_id = request.form.get('track_id')
            track = Track.query.get_or_404(track_id)
            
            if track:
                track_name = request.form.get('name')
                safe_name = secure_filename(track_name)
                
                track.name = track_name
                track.description = request.form.get('description', track.description)

                # Handle audio file update
                if 'file' in request.files and request.files['file'].filename != '':
                    music_file = request.files['file']
                    if track.file:
                        old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], track.file)
                        if os.path.exists(old_file_path):
                            os.remove(old_file_path)
                    file_ext = os.path.splitext(music_file.filename)[1]
                    music_filename = safe_name + file_ext
                    music_file.save(os.path.join(app.config['UPLOAD_FOLDER'], music_filename))
                    track.file = music_filename

                # Handle primary artwork update
                if 'artwork' in request.files and request.files['artwork'].filename != '':
                    artwork = request.files['artwork']
                    if track.artwork and track.artwork != "No Artwork":
                        old_artwork_path = os.path.join(app.config['UPLOAD_FOLDER'], track.artwork)
                        if os.path.exists(old_artwork_path):
                            os.remove(old_artwork_path)
                    art_ext = os.path.splitext(artwork.filename)[1]
                    artwork_filename = safe_name + "_artwork" + art_ext
                    artwork.save(os.path.join(app.config['UPLOAD_FOLDER'], artwork_filename))
                    track.artwork = artwork_filename

                # Handle secondary artwork update
                if 'artwork_secondary' in request.files and request.files['artwork_secondary'].filename != '':
                    secondary = request.files['artwork_secondary']
                    if track.artwork_secondary and track.artwork_secondary != "No Secondary Artwork":
                        old_secondary_path = os.path.join(app.config['UPLOAD_FOLDER'], track.artwork_secondary)
                        if os.path.exists(old_secondary_path):
                            os.remove(old_secondary_path)
                    sec_ext = os.path.splitext(secondary.filename)[1]
                    secondary_filename = safe_name + "_secondary" + sec_ext
                    secondary.save(os.path.join(app.config['UPLOAD_FOLDER'], secondary_filename))
                    track.artwork_secondary = secondary_filename

                db.session.commit()
                flash('Track updated successfully!', 'success')

        return redirect(url_for('admin_panel'))

    return render_template('admin.html', tracks=tracks, form=form, latest_track=latest_track)

@app.route('/download_tracks', methods=['POST'])
@login_required
@admin_required
def download_tracks():
    try:
        data = request.get_json()
        track_ids = data.get('track_ids', [])
        
        if not track_ids:
            return jsonify({'success': False, 'message': 'No tracks selected'}), 400
            
        tracks = Track.query.filter(Track.id.in_(track_ids)).all()
        files_info = []
        
        for track in tracks:
            if track.file:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], track.file)
                if os.path.exists(file_path):
                    files_info.append({
                        'name': track.name,
                        'url': url_for('static', filename=f'uploads/{track.file}', _external=True)
                    })

        if not files_info:
            return jsonify({'success': False, 'message': 'No files available for download'}), 404

        return jsonify({
            'success': True,
            'files': files_info,
            'message': 'Files ready for download'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/delete_tracks', methods=['POST'])
@login_required
@admin_required
def delete_tracks():
    data = request.get_json()
    track_ids = data.get('track_ids', [])
    
    try:
        for track_id in track_ids:
            track = Track.query.get_or_404(track_id)
            
            # Delete associated files
            if track.artwork and track.artwork != "No Artwork":
                artwork_path = os.path.join(app.config['UPLOAD_FOLDER'], track.artwork)
                if os.path.exists(artwork_path):
                    os.remove(artwork_path)
                    
            if track.file:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], track.file)
                if os.path.exists(file_path):
                    os.remove(file_path)

            db.session.delete(track)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Tracks deleted successfully!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/logout')
@login_required
def logout():
    """Log out the current user"""
    logout_user()
    return redirect(url_for('index'))

@app.route('/remove_artwork', methods=['POST'])
@login_required
@admin_required
def remove_artwork():
    """Remove artwork from a track"""
    track_id = request.form.get('track_id')
    track = Track.query.get(track_id)
    
    if track and track.artwork_filename:
        artwork_path = os.path.join(app.config['UPLOAD_FOLDER'], 'artwork', track.artwork_filename)
        if os.path.exists(artwork_path):
            os.remove(artwork_path)
        
        track.artwork_filename = None
        db.session.commit()
        
    return redirect(url_for('admin_panel'))

# Like track route
@app.route('/track/like/<int:track_id>', methods=['POST'])
def like_track(track_id):
    track = Track.query.get_or_404(track_id)
    track.like_count = track.like_count + 1 if track.like_count else 1
    db.session.commit()
    return jsonify({'success': True, 'like_count': track.like_count})

# Unlike track route
@app.route('/track/unlike/<int:track_id>', methods=['POST'])
def unlike_track(track_id):
    track = Track.query.get_or_404(track_id)
    track.unlike_count = track.unlike_count + 1 if track.unlike_count else 1
    db.session.commit()
    return jsonify({'success': True, 'unlike_count': track.unlike_count})

# Clear likes for a track
@app.route('/track/clear-likes/<int:track_id>', methods=['POST'])
@login_required
@admin_required
def clear_likes(track_id):
    track = Track.query.get_or_404(track_id)
    track.like_count = 0
    db.session.commit()
    return jsonify({'success': True})

# Clear unlikes for a track
@app.route('/track/clear-unlikes/<int:track_id>', methods=['POST'])
@login_required
@admin_required
def clear_unlikes(track_id):
    track = Track.query.get_or_404(track_id)
    track.unlike_count = 0
    db.session.commit()
    return jsonify({'success': True})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create admin user if it doesn't exist
        admin_user = User.query.filter_by(username=os.getenv('ADMIN_USER')).first()
        if not admin_user:
            admin_user = User(
                username=os.getenv('ADMIN_USER'),
                password=generate_password_hash(os.getenv('ADMIN_PASSWORD')),
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
    app.run(debug=True, port=5002)