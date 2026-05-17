from flask import Flask, jsonify
from config import config
from utils import ensure_directory_exists, cleanup_expired_files
from routes import register_blueprints

app = Flask(__name__)

app_config = config['default']
app.config.from_object(app_config)
app_config.init_app(app)
app.config['MAX_CONTENT_LENGTH'] = getattr(app_config, 'MAX_CONTENT_LENGTH', app.config.get('MAX_CONTENT_LENGTH'))

ensure_directory_exists(app.config['UPLOAD_FOLDER'])
ensure_directory_exists(app.config['CONVERTED_FOLDER'])
cleanup_expired_files(app.config['CONVERTED_FOLDER'], app.config['FILE_EXPIRY_SECONDS'])

register_blueprints(app)

@app.route('/')
def index():
    return jsonify({'success': True, 'message': 'NOBZ BEATS - Audio Tools API (analyze, convert, separate)'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5002)
