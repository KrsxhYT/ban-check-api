from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)

# ------------------------------------------------- CONFIG --------------------------------------------------------------------------------------
BANCHECK_API_URL = "https://ff.garena.com/api/antihack/check_banned?lang=en&uid={uid}"
SHOP2GAME_API_URL = "https://shop2game.com/api/auth/player_id_login"
# -----------------------------------------------------------------------------------------------------------------------------------------------------

BANCHECK_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'authority': 'ff.garena.com',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'referer': 'https://ff.garena.com/en/support/',
    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'x-requested-with': 'B6FksShzIgjfrYImLpTsadjS86sddhFH',
}

SHOP2GAME_COOKIES = {
    '_ga': 'GA1.1.2123120599.1674510784',
    '_fbp': 'fb.1.1674510785537.363500115',
    '_ga_7JZFJ14B0B': 'GS1.1.1674510784.1.1.1674510789.0.0.0',
    'source': 'mb',
    'region': 'MA',
    'language': 'ar',
    '_ga_TVZ1LG7BEB': 'GS1.1.1674930050.3.1.1674930171.0.0.0',
    'datadome': '6h5F5cx_GpbuNtAkftMpDjsbLcL3op_5W5Z-npxeT_qcEe_7pvil2EuJ6l~JlYDxEALeyvKTz3~LyC1opQgdP~7~UDJ0jYcP5p20IQlT3aBEIKDYLH~cqdfXnnR6FAL0',
    'session_key': 'efwfzwesi9ui8drux4pmqix4cosane0y',
}

SHOP2GAME_HEADERS = {
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
    'Origin': 'https://shop2game.com',
    'Referer': 'https://shop2game.com/app/100067/idlogin',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Redmi Note 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36',
    'accept': 'application/json',
    'content-type': 'application/json',
    'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
    'x-datadome-clientid': '6h5F5cx_GpbuNtAkftMpDjsbLcL3op_5W5Z-npxeT_qcEe_7pvil2EuJ6l~JlYDxEALeyvKTz3~LyC1opQgdP~7~UDJ0jYcP5p20IQlT3aBEIKDYLH~cqdfXnnR6FAL0',
}

def is_valid_uid(uid: str) -> bool:
    return uid.isdigit() and 8 <= len(uid) <= 11

def check_player_info(uid: str):
    """Check player info with ban status"""
    start_time = time.time()
    
    if not is_valid_uid(uid):
        return {
            "error": True,
            "message": "Invalid UID (must be 8-11 digits)"
        }
    
    try:
        # Get player info from shop2game
        json_data = {
            'app_id': 100067,
            'login_id': uid,
            'app_server_id': 0,
        }
        
        res = requests.post(
            SHOP2GAME_API_URL,
            cookies=SHOP2GAME_COOKIES,
            headers=SHOP2GAME_HEADERS,
            json=json_data,
            timeout=10
        )
        
        if res.status_code != 200 or not res.json().get('nickname'):
            return {
                "error": True,
                "message": "Player ID not found"
            }
        
        player_data = res.json()
        nickname = player_data.get('nickname', 'N/A')
        region = player_data.get('region', 'N/A')
        level = player_data.get('level', 'N/A')
        likes = player_data.get('likes', 'N/A')
        
        # Get ban status
        ban_response = requests.get(
            BANCHECK_API_URL.format(uid=uid),
            headers=BANCHECK_HEADERS,
            timeout=10
        )
        
        if ban_response.status_code == 200:
            ban_data = ban_response.json().get("data", {})
            period = ban_data.get("period", 0)
            is_banned = period != 0 if period is not None else False
            reason = ban_data.get("reason") or ban_data.get("desc") or "No reason provided"
            
            if is_banned:
                ban_status = "Banned ❌"
                ban_period = f"{period} months" if period > 0 else "Permanent"
            else:
                ban_status = "Not Banned ✅"
                ban_period = "0 months"
            
            response_time = f"{round((time.time() - start_time) * 1000)}ms"
            
            return {
                "success": True,
                "uid": uid,
                "nickname": nickname,
                "level": level,
                "likes": likes,
                "region": region,
                "ban_status": ban_status,
                "period": ban_period,
                "reason": reason,
                "response_time": response_time,
                "gif": "https://files.catbox.moe/lns4kb.gif" if is_banned else "https://files.catbox.moe/7to40v.gif"
            }
        else:
            return {
                "error": True,
                "message": "Failed to retrieve ban status"
            }
            
    except requests.exceptions.Timeout:
        return {
            "error": True,
            "message": "Request timeout"
        }
    except requests.exceptions.ConnectionError:
        return {
            "error": True,
            "message": "Connection error"
        }
    except Exception as e:
        return {
            "error": True,
            "message": f"Request failed: {str(e)}"
        }

# ============================================
# API ENDPOINTS
# ============================================

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "Free Fire Player Info & Ban Check API",
        "endpoints": {
            "GET /check/<uid>": "Get player info & ban status by UID",
            "GET /check?uid=<uid>": "Get player info & ban status via query",
            "POST /check": "Get player info & ban status via POST"
        },
        "response_fields": [
            "uid",
            "nickname",
            "level",
            "likes",
            "region",
            "ban_status",
            "period",
            "reason",
            "response_time",
            "gif"
        ],
        "author": "Krsxh@blackhat"
    })

@app.route('/check/<uid>', methods=['GET'])
def check_by_path(uid):
    """Get player info with ban status"""
    result = check_player_info(uid)
    return jsonify(result)

@app.route('/check', methods=['GET'])
def check_by_query():
    """Check by query parameter"""
    uid = request.args.get('uid')
    
    if not uid:
        return jsonify({
            "error": True,
            "message": "UID parameter is required",
            "example": "/check?uid=2919267964"
        }), 400
    
    result = check_player_info(uid)
    return jsonify(result)

@app.route('/check', methods=['POST'])
def check_by_post():
    """Check via POST request"""
    if request.is_json:
        data = request.get_json()
        uid = data.get('uid')
    else:
        uid = request.form.get('uid')
    
    if not uid:
        return jsonify({
            "error": True,
            "message": "UID is required in request body",
            "example": {"uid": "2919267964"}
        }), 400
    
    result = check_player_info(uid)
    return jsonify(result)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "ff-player-check",
        "version": "3.0.0"
    })

@app.route('/batch', methods=['POST'])
def batch_check():
    if request.is_json:
        data = request.get_json()
        uids = data.get('uids', [])
    else:
        uids_str = request.form.get('uids', '')
        uids = uids_str.split(',') if uids_str else []
    
    if not uids:
        return jsonify({
            "error": True,
            "message": "uids parameter is required",
            "example": {"uids": ["2919267964", "12345678"]}
        }), 400
    
    if len(uids) > 10:
        return jsonify({
            "error": True,
            "message": "Maximum 10 UIDs allowed per batch"
        }), 400
    
    results = []
    for uid in uids:
        uid = str(uid).strip()
        result = check_player_info(uid)
        results.append(result)
    
    return jsonify({
        "success": True,
        "count": len(results),
        "results": results
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": True,
        "message": "Endpoint not found",
        "available_endpoints": ["/", "/check", "/check/<uid>", "/health", "/batch"]
    }), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({
        "error": True,
        "message": "Internal server error"
    }), 500

if __name__ == '__main__':
    app.run(debug=True)
