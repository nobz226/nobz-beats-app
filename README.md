# NOBZ BEATS APP

> *Where Music Production Meets Innovation*
> 
> *This is a project built using a combination of AI and handwritten code and is still a work in progress.*

<div align="center">
  <img src="static/images/bg3.png" alt="Music Production Toolkit" width="100%"/>
  <h1 style="position: relative; margin-top: -80px; color: #ffffff; text-shadow: 0 0 10px #ff00ff, 0 0 20px #00ffff; font-size: 3em; font-weight: 800;">NOBZ BEATS</h1>
</div>

<div align="center">
  
  [![YouTube](https://img.shields.io/badge/YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://www.youtube.com/@nobz_beats7894)
  [![SoundCloud](https://img.shields.io/badge/SoundCloud-FF3300?style=for-the-badge&logo=soundcloud&logoColor=white)](https://soundcloud.com/user-621182531)
  
</div>

---

## Overview

NOBZ BEATS APP is a comprehensive music production web application that combines audio processing tools, track showcase capabilities, and AI-powered production assistance. Built with Flask and modern web technologies, this application provides producers and music enthusiasts with professional-grade tools for audio analysis, stem separation, format conversion, and more.

---

## Features

### Music Showcase
- Browse and play original beats and remixes
- Responsive audio player with vinyl spinning animation
- Track likes and play count tracking
- Global audio player with visualizer
- Upload and manage tracks through admin panel

### Audio Analysis
- Analyze audio files to determine key and tempo
- Instant BPM and key detection using librosa
- Supports multiple audio formats (MP3, WAV, FLAC)
- Accurate musical key detection for harmonic mixing

### Stem Separator
- Split tracks into separate stems (vocals, drums, bass, melody)
- Download isolated components for remixing
- Powered by Demucs high-quality audio separation model
- Professional-grade stem extraction for production workflows

### Format Converter
- Convert audio files between different formats (MP3, WAV, FLAC)
- Simple drag-and-drop interface
- Fast processing with automatic download
- High-quality conversion using FFmpeg

### AI Production Assistant
- Interactive AI chatbot (Alex) for music production advice
- Powered by LLaMA 3.3 70B via Together API
- Instant answers to music production questions
- Tips on beatmaking, mixing, and music theory
- Context-aware responses based on production knowledge

### Design Features
- Responsive design for mobile and desktop
- Custom vinyl loading animation
- Dark theme optimized for producers
- Modern UI with smooth animations
- Global audio player that persists across pages

---

## Tech Stack

<div align="center">
  
  ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
  ![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
  ![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
  ![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
  
</div>

### Backend
- **Framework**: Flask (Python 3.8+)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Flask-Login for user management
- **Audio Processing**:
  - librosa - Advanced audio analysis
  - demucs - AI-powered stem separation
  - FFmpeg - Professional audio format conversion
- **AI Integration**: LLaMA 3.3 70B via Together API

### Frontend
- **JavaScript**: Vanilla JavaScript for client-side logic
- **CSS**: Custom stylesheets with modern animations
- **Design**: Responsive mobile-first approach
- **Audio Player**: Custom global audio player with visualizer

### Architecture
- **Blueprint-based routing** for modular organization
- **Service layer pattern** for audio processing operations
- **Configuration management** with environment-specific settings
- **Session-based file management** with automatic cleanup

---

## Installation

### Prerequisites
- Python 3.8 or higher
- FFmpeg installed and available in system PATH
- Together API key for AI features

### Setup Instructions

**1. Clone the repository**
```bash
git clone https://github.com/nobz226/nobz-beats-app.git
cd nobz-beats-app
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set up environment variables**

Create a `.env` file in the project root:
```
TOGETHER_API_KEY=your_together_api_key_here
ADMIN_USER=your_admin_username
ADMIN_PASSWORD=your_admin_password
```

**5. Initialize the database**
```bash
flask shell
>>> from app import db
>>> db.create_all()
>>> exit()
```

**6. Run the application**
```bash
python app.py
```

**7. Access the application**

Open your browser and navigate to `http://localhost:5000`

---

## Project Structure

```
nobz-beats-app/
│
├── app.py                    # Main application file with core routes
├── config.py                 # Configuration settings for different environments
├── extensions.py             # Flask extensions initialization
├── forms.py                  # Flask-WTF form classes
├── models.py                 # Database models (User, Track)
├── services.py               # Audio processing services
├── utils.py                  # Utility functions for file handling
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (create this)
│
├── routes/                   # Blueprint routes (modular routing)
│   └── ...
│
├── static/                   # Static files
│   ├── css/                  # Stylesheets
│   │   ├── base.css          # Base styles
│   │   ├── hero.css          # Hero section styles
│   │   ├── navigation.css    # Navigation styles
│   │   ├── audio-player.css  # Audio player styles
│   │   └── ...               # Other style files
│   ├── js/                   # JavaScript files
│   ├── fonts/                # Custom fonts
│   ├── images/               # Images and graphics
│   ├── uploads/              # Uploaded audio files
│   └── converted/            # Processed audio files
│
├── templates/                # HTML templates
│   ├── base.html             # Base template with global player
│   ├── home.html             # Homepage
│   ├── about.html            # About page
│   ├── showcase.html         # Track showcase
│   ├── analyzer.html         # Audio analysis tool
│   ├── separator.html        # Stem separator tool
│   ├── converter.html        # Format converter tool
│   ├── guides.html           # Production guides with AI chatbot
│   └── admin.html            # Admin panel
│
└── instance/                 # Instance-specific files
    └── app.db                # SQLite database (generated)
```

---

## Usage Guide

### Audio Analysis
1. Navigate to the "Audio Analyzer" page
2. Upload an audio file (MP3, WAV, or FLAC)
3. Click "Analyze"
4. View the detected BPM and musical key
5. Use this information for harmonic mixing or tempo matching

### Stem Separation
1. Go to the "Stem Separator" page
2. Upload a complete song file
3. Click "Separate Stems"
4. Wait for processing (this may take a few minutes)
5. Download individual stems (vocals, drums, bass, melody)
6. Use stems for remixing or sampling

### Format Conversion
1. Access the "Format Converter" page
2. Upload an audio file
3. Select the desired output format (MP3, WAV, or FLAC)
4. Click "Convert"
5. Download the converted file automatically

### AI Production Guide
1. Open the "Production Guides" page
2. Type a question about music production in the chat
3. Receive instant guidance from Alex, the AI production assistant
4. Use suggested topics or ask custom questions
5. Get advice on beatmaking, mixing, mastering, and music theory

### Track Showcase
1. Browse available tracks on the "Showcase" page
2. Click on any track to play it in the global audio player
3. Like tracks to show appreciation
4. View play counts and popularity metrics

---

## Admin Features

### Authentication
- Secure login system using Flask-Login
- Password hashing with Werkzeug security
- Admin-only access to management features

### Track Management
- Upload new tracks with custom artwork
- Edit track information (name, description)
- Delete tracks from the showcase
- Manage the complete track library
- View track statistics (plays, likes)

### File Management
- Automatic file handling and storage
- Secure filename processing
- Session-based cleanup for temporary files

---

## API Integration

### Together AI API
The application integrates with the Together AI API to provide production assistance through the LLaMA 3.3 70B model. The AI assistant is configured with:
- Music production knowledge base
- Context-aware responses
- Streaming support for real-time interaction

---

## Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and test thoroughly
4. Commit your changes: `git commit -m 'Add amazing feature'`
5. Push to the branch: `git push origin feature/amazing-feature`
6. Open a pull request with a clear description

### Guidelines
- Follow the existing code style
- Add comments for complex logic
- Test all features before submitting
- Update documentation for new features

---

## Future Enhancements

- User account system with personalized playlists
- Advanced audio effects and processing
- Real-time collaboration features
- Mobile app development
- Integration with major streaming platforms
- Enhanced AI features with voice interaction
- Community features and social sharing

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Connect With Me

<div align="center">
  
  [![YouTube](https://img.shields.io/badge/YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://www.youtube.com/@nobz_beats7894)
  [![SoundCloud](https://img.shields.io/badge/SoundCloud-FF3300?style=for-the-badge&logo=soundcloud&logoColor=white)](https://soundcloud.com/user-621182531)
  
</div>

---

## Acknowledgments

- [Demucs](https://github.com/facebookresearch/demucs) - Facebook Research's stem separation technology
- [librosa](https://librosa.org/) - Python library for audio analysis
- [LLaMA](https://ai.meta.com/llama/) - Meta's large language model for AI features
- [Together](https://www.together.ai/) - AI API services for production assistant
- [Flask](https://flask.palletsprojects.com/) - Web framework for Python
- [FFmpeg](https://ffmpeg.org/) - Complete audio/video processing solution

---

<div align="center">
  
  ### Made with passion by NOBZ BEATS
  
  *Empowering music producers with cutting-edge tools and AI assistance*
  
</div>