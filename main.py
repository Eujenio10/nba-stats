from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib
import os
from functools import wraps
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///keys.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Key model
class ApiKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key_hash = db.Column(db.String(256), unique=True, nullable=False)
    expiry_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Create tables
with app.app_context():
    db.create_all()

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({"error": "API key is missing"}), 401
        
        # Verify key
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key_record = ApiKey.query.filter_by(key_hash=key_hash).first()
        
        if not key_record or key_record.expiry_date < datetime.now():
            return jsonify({"error": "Invalid or expired API key"}), 401
            
        return f(*args, **kwargs)
    return decorated

@app.route('/api/verify-key', methods=['POST'])
def verify_key():
    data = request.get_json()
    key = data.get('key')
    
    if not key:
        return jsonify({"error": "Key is required"}), 400
        
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    key_record = ApiKey.query.filter_by(key_hash=key_hash).first()
    
    if key_record and key_record.expiry_date > datetime.now():
        return jsonify({
            "valid": True,
            "expiry_date": key_record.expiry_date.strftime("%Y-%m-%d")
        })
    
    return jsonify({"valid": False, "error": "Invalid or expired key"}), 401

@app.route('/api/stats/defensive-ranking', methods=['GET'])
@require_api_key
def get_defensive_ranking():
    # Implement your defensive ranking logic here
    return jsonify({"message": "Defensive ranking endpoint"})

@app.route('/api/stats/injured-players', methods=['GET'])
@require_api_key
def get_injured_players():
    # Implement your injured players logic here
    return jsonify({"message": "Injured players endpoint"})

@app.route('/api/stats/upcoming-games', methods=['GET'])
@require_api_key
def get_upcoming_games():
    # Implement your upcoming games logic here
    return jsonify({"message": "Upcoming games endpoint"})

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 