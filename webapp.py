from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib
import os
from functools import wraps
from dotenv import load_dotenv
import json
import threading

# Importiamo le funzioni dal nostro script originale
import nba_stats_appv as nba

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
    machine_id = db.Column(db.String(256), nullable=True)  # Machine ID associato alla chiave
    expiry_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime, nullable=True)
    is_blocked = db.Column(db.Boolean, default=False)  # Per bloccare chiavi violate

# Create tables
with app.app_context():
    db.create_all()

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        machine_id = request.headers.get('X-Machine-ID')
        
        if not api_key:
            return jsonify({"error": "API key is missing"}), 401
            
        if not machine_id:
            return jsonify({"error": "Machine ID is missing"}), 401
        
        # Verify key
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key_record = ApiKey.query.filter_by(key_hash=key_hash).first()
        
        # Controllo se la chiave esiste e non è scaduta
        if not key_record or key_record.expiry_date < datetime.now() or key_record.is_blocked:
            return jsonify({"error": "Invalid or expired API key"}), 401
        
        # Se la chiave non ha ancora un machine_id associato, lo registriamo
        if key_record.machine_id is None:
            key_record.machine_id = machine_id
            db.session.commit()
        
        # Verifica che il machine_id corrisponda a quello registrato
        elif key_record.machine_id != machine_id:
            # Registra il tentativo di violazione
            key_record.is_blocked = True
            db.session.commit()
            return jsonify({"error": "This key is registered to another device"}), 401
            
        # Aggiorna l'ultimo utilizzo
        key_record.last_used = datetime.now()
        db.session.commit()
            
        return f(*args, **kwargs)
    return decorated

@app.route('/api/verify-key', methods=['POST'])
def verify_key():
    data = request.get_json()
    key = data.get('key')
    machine_id = data.get('machine_id')
    
    if not key or not machine_id:
        return jsonify({"error": "Both key and machine_id are required"}), 400
        
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    key_record = ApiKey.query.filter_by(key_hash=key_hash).first()
    
    if not key_record or key_record.expiry_date < datetime.now() or key_record.is_blocked:
        return jsonify({"valid": False, "error": "Invalid or expired key"}), 401
    
    # Se la chiave non ha ancora un machine_id associato, lo registriamo
    if key_record.machine_id is None:
        key_record.machine_id = machine_id
        key_record.last_used = datetime.now()
        db.session.commit()
        return jsonify({
            "valid": True,
            "expiry_date": key_record.expiry_date.strftime("%Y-%m-%d")
        })
    
    # Verifica che il machine_id corrisponda a quello registrato
    if key_record.machine_id != machine_id:
        return jsonify({
            "valid": False, 
            "error": "This key is registered to another device"
        }), 401
    
    # Aggiorna l'ultimo utilizzo
    key_record.last_used = datetime.now()
    db.session.commit()
    
    return jsonify({
        "valid": True,
        "expiry_date": key_record.expiry_date.strftime("%Y-%m-%d")
    })

# Endpoint di amministrazione per generare nuove chiavi (protetto da password admin)
@app.route('/api/admin/generate-key', methods=['POST'])
def generate_key():
    data = request.get_json()
    admin_password = data.get('admin_password')
    expiry_days = data.get('expiry_days', 365)  # Default 1 anno
    
    # Verifica password admin (in produzione usare un metodo più sicuro)
    if admin_password != os.getenv('ADMIN_PASSWORD'):
        return jsonify({"error": "Unauthorized"}), 401
    
    # Genera una nuova chiave
    new_key = hashlib.sha256(os.urandom(32)).hexdigest()[:32]  # 32 caratteri
    key_hash = hashlib.sha256(new_key.encode()).hexdigest()
    
    # Calcola la data di scadenza
    expiry_date = datetime.now().replace(
        hour=23, minute=59, second=59
    )
    expiry_date = expiry_date.replace(day=expiry_date.day + expiry_days)
    
    # Salva nel database
    api_key = ApiKey(
        key_hash=key_hash,
        expiry_date=expiry_date
    )
    db.session.add(api_key)
    db.session.commit()
    
    return jsonify({
        "key": new_key,
        "expiry_date": expiry_date.strftime("%Y-%m-%d")
    })

# ---- NBA STATS API ENDPOINTS ----

@app.route('/api/stats/team-defense', methods=['GET'])
@require_api_key
def get_team_defense():
    # Utilizziamo la funzione originale dal file nba_stats_appv.py
    try:
        sort_by_points = request.args.get('sort_by_points', 'true').lower() == 'true'
        result = nba.get_team_defensive_ranking(sort_by_points=sort_by_points)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats/injured-players', methods=['GET'])
@require_api_key
def get_injured_players():
    # Utilizziamo la funzione originale dal file nba_stats_appv.py
    try:
        result = nba.get_injured_players()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats/upcoming-games', methods=['GET'])
@require_api_key
def get_upcoming_games():
    # Utilizziamo la funzione originale dal file nba_stats_appv.py
    try:
        result = nba.get_upcoming_games()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats/player', methods=['GET'])
@require_api_key
def get_player_stats():
    # Utilizziamo la funzione originale dal file nba_stats_appv.py
    try:
        player_name = request.args.get('name')
        if not player_name:
            return jsonify({"error": "Player name is required"}), 400
        
        result = nba.get_player_stats(player_name)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats/player/last-games', methods=['GET'])
@require_api_key
def get_player_last_games():
    # Utilizziamo la funzione originale dal file nba_stats_appv.py
    try:
        player_name = request.args.get('name')
        num_games = request.args.get('num_games', 10)
        
        if not player_name:
            return jsonify({"error": "Player name is required"}), 400
        
        try:
            num_games = int(num_games)
        except ValueError:
            return jsonify({"error": "num_games must be a number"}), 400
        
        result = nba.get_player_last_games(player_name, num_games)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats/player/analyze-trends', methods=['GET'])
@require_api_key
def analyze_player_trends():
    # Utilizziamo la funzione originale dal file nba_stats_appv.py
    try:
        player_name = request.args.get('name')
        prop_type = request.args.get('prop_type')
        line_value = request.args.get('line_value')
        
        if not player_name or not prop_type or not line_value:
            return jsonify({"error": "name, prop_type and line_value are required"}), 400
        
        try:
            line_value = float(line_value)
        except ValueError:
            return jsonify({"error": "line_value must be a number"}), 400
        
        result = nba.analyze_player_trends(player_name, prop_type, line_value)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats/consistent-players', methods=['GET'])
@require_api_key
def get_consistent_players():
    # Utilizziamo la funzione originale dal file nba_stats_appv.py
    try:
        result = nba.find_consistent_players()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats/player-vs-team', methods=['GET'])
@require_api_key
def get_player_vs_team():
    # Utilizziamo la funzione originale dal file nba_stats_appv.py
    try:
        player_name = request.args.get('name')
        team_abbr = request.args.get('team')
        num_games = request.args.get('num_games', 10)
        
        if not player_name or not team_abbr:
            return jsonify({"error": "name and team are required"}), 400
        
        try:
            num_games = int(num_games)
        except ValueError:
            return jsonify({"error": "num_games must be a number"}), 400
        
        result = nba.get_player_vs_team_games(player_name, team_abbr, num_games)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats/next-opponent', methods=['GET'])
@require_api_key
def get_next_opponent():
    # Utilizziamo la funzione originale dal file nba_stats_appv.py
    try:
        player_name = request.args.get('name')
        
        if not player_name:
            return jsonify({"error": "Player name is required"}), 400
        
        result = nba.get_next_opponent(player_name)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 