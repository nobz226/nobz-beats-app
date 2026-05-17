from flask import Flask, jsonify, render_template
import os
from config import config
from utils import ensure_directory_exists, cleanup_expired_files
from routes import register_blueprints

# Minimal Flask app focused on audio tools: analyzer, converter, separator

app = Flask(__name__)

# Load configuration (default)
app_config = config['default']
app.config.from_object(app_config)
app_config.init_app(app)

# Enforce maximum upload size (Flask will reject requests larger than this)
app.config['MAX_CONTENT_LENGTH'] = getattr(app_config, 'MAX_CONTENT_LENGTH', app.config.get('MAX_CONTENT_LENGTH'))

ensure_directory_exists(app.config['UPLOAD_FOLDER'])
ensure_directory_exists(app.config['CONVERTED_FOLDER'])
cleanup_expired_files(app.config['CONVERTED_FOLDER'], app.config['FILE_EXPIRY_SECONDS'])


# Routes

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