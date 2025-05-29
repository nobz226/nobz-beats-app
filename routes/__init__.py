from routes.audio import audio_bp

# List of all blueprints
all_blueprints = [audio_bp]

def register_blueprints(app):
    """Register all blueprints with the Flask app."""
    for blueprint in all_blueprints:
        app.register_blueprint(blueprint) 