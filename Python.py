from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
import requests
import json
import time
import hmac
import hashlib
import base64
import math
import os

app = Flask(__name__, static_folder='.')
CORS(app)

# ============================================
# TOKEN GENERATOR
# ============================================
SECRET = "GAMESKINBOFFIDCHECKERSECURITYPROTOCOL"

def generate_token(uid: str) -> str:
    timestamp_ms = int(time.time() * 1000)
    time_block = math.floor(timestamp_ms / 30000)
    nonce = hmac.new(
        SECRET.encode(),
        str(time_block).encode(),
        hashlib.sha256
    ).hexdigest()[:32]
    signature = hmac.new(
        nonce.encode(),
        f"{uid}|{timestamp_ms}".encode(),
        hashlib.sha256
    ).hexdigest()
    raw = f"{uid}|{timestamp_ms}|{signature}"
    return base64.b64encode(raw.encode()).decode()

# ============================================
# FF PLAYER DATA FETCH
# ============================================
def fetch_ff_player(uid, region="IND"):
    """Fetch Free Fire player data from multiple sources"""
    
    # Method 1: Games Kinbo API
    try:
        token = generate_token(uid)
        url = f"https://gameskinbo.com/api/ff_id_checker?uid={uid}&token={token}&region={region.lower()}"
        
        headers = {
            'authority': 'gameskinbo.com',
            'accept': '*/*',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'x-api-client': 'gameskinbo-web',
            'referer': 'https://gameskinbo.com/free_fire_id_checker',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('name'):
                return {
                    'success': True,
                    'source': 'Games Kinbo',
                    'data': {
                        'nickname': data.get('name'),
                        'accountId': uid,
                        'level': data.get('level'),
                        'region': data.get('region', region),
                        'likes': data.get('likes', 0),
                        'exp': data.get('exp', 0),
                        'gender': data.get('gender'),
                        'guild': data.get('guild_name'),
                        'guildLevel': data.get('guild_level'),
                        'brRank': data.get('br_max_rank'),
                        'brRankPoint': data.get('br_rank_point'),
                        'csRank': data.get('cs_max_rank'),
                        'csRankPoint': data.get('cs_rank_point'),
                        'created': data.get('created_at'),
                        'lastLogin': data.get('last_login'),
                        'honorScore': data.get('honor_score'),
                        'creditScore': data.get('credit_score'),
                        'primeLevel': data.get('prime_level'),
                        'signature': data.get('signature'),
                    }
                }
    except Exception as e:
        print(f"Games Kinbo error: {e}")

    # Method 2: Alternative API
    try:
        url = f"https://ff.garena.com/api/anticheat/player_profile?uid={uid}&region={region.lower()}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('player_profile'):
                p = data['player_profile']
                return {
                    'success': True,
                    'source': 'Garena API',
                    'data': {
                        'nickname': p.get('nickname') or p.get('name'),
                        'accountId': uid,
                        'level': p.get('level'),
                        'region': p.get('region', region),
                        'likes': p.get('likes', 0),
                        'exp': p.get('exp', 0),
                        'gender': p.get('gender'),
                        'guild': p.get('guild_name'),
                        'brRank': p.get('br_max_rank'),
                        'csRank': p.get('cs_max_rank'),
                        'created': p.get('created_at'),
                        'lastLogin': p.get('last_login'),
                    }
                }
    except Exception as e:
        print(f"Garena API error: {e}")

    # Method 3: Backup API
    try:
        url = f"https://freefireinfo-zy9l.onrender.com/api/v1/player-profile?uid={uid}&region={region}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            player = data.get('data', data)
            if player.get('nickname'):
                return {
                    'success': True,
                    'source': 'FreeFire Info',
                    'data': {
                        'nickname': player.get('nickname'),
                        'accountId': uid,
                        'level': player.get('level'),
                        'region': player.get('region', region),
                        'likes': player.get('liked', 0),
                        'exp': player.get('exp', 0),
                        'guild': player.get('guild'),
                        'brRank': player.get('br_rank'),
                        'csRank': player.get('cs_rank'),
                        'created': player.get('created_at'),
                        'lastLogin': player.get('last_login'),
                    }
                }
    except Exception as e:
        print(f"Backup API error: {e}")

    return {'success': False, 'error': 'Player not found'}

# ============================================
# ROUTES
# ============================================
@app.route('/')
def index():
    # Render par static file serve karna
    try:
        return send_from_directory('.', 'index.html')
    except:
        return jsonify({
            'message': 'FF UID Checker API is running!',
            'endpoints': {
                '/api/player?uid=UID&region=REGION': 'Get player info',
                '/api/regions': 'Get all regions'
            }
        })

@app.route('/api/player')
def get_player():
    uid = request.args.get('uid')
    region = request.args.get('region', 'IND')
    
    if not uid:
        return jsonify({'error': 'UID required'}), 400
    
    if not uid.isdigit() or len(uid) < 6:
        return jsonify({'error': 'Invalid UID format'}), 400
    
    result = fetch_ff_player(uid, region)
    
    if result['success']:
        return jsonify({
            'success': True,
            'source': result['source'],
            'data': result['data']
        })
    else:
        return jsonify({
            'success': False,
            'error': result.get('error', 'Player not found. Try different region.')
        }), 404

@app.route('/api/regions')
def get_regions():
    return jsonify({
        'regions': ['IND', 'BD', 'ID', 'SG', 'PK', 'BR', 'US', 'TH', 'VN', 'TW']
    })

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'message': 'Server is running!'})

# ============================================
# RENDER.COM KE LIYE
# ============================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
