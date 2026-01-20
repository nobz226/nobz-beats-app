from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from extensions import db
from datetime import datetime

# Association table for many-to-many relationship between playlists and tracks
playlist_tracks = db.Table('playlist_tracks',
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlists.id'), primary_key=True),
    db.Column('track_id', db.Integer, db.ForeignKey('tracks.id'), primary_key=True)
)

# User model for authentication
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to playlists
    playlists = db.relationship('Playlist', backref='owner', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'

# Track model with like and unlike counts
class Track(db.Model):
    __tablename__ = 'tracks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    file = db.Column(db.String(200), nullable=False)
    artwork = db.Column(db.String(200), nullable=True)
    artwork_secondary = db.Column(db.String(200), nullable=True)
    play_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)  # New field for likes
    unlike_count = db.Column(db.Integer, default=0)  # New field for unlikes
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Track {self.name}>'


# Playlist model
class Playlist(db.Model):
    __tablename__ = 'playlists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Many-to-many relationship with tracks
    tracks = db.relationship('Track', secondary=playlist_tracks, backref='in_playlists', lazy='dynamic')

    def __repr__(self):
        return f'<Playlist {self.name}>'