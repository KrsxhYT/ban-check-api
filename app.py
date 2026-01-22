from flask import Flask, request, jsonify
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for web usage

# ------------------------------------------------- CONFIG --------------------------------------------------------------------------------------
BANCHECK_API_URL = "https://ff.garena.com/api/antihack/check_banned?lang=en&uid={uid}"
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

def is_valid_uid(uid: str) -> bool:
    """Check if UID is valid (8-11 digits)"""
    return uid.isdigit() and 8 <= len(uid) <= 11

def convert_ban_period_to_status(period_value):
    """Convert ban period to human-readable status"""
    try:
        period = int(period_value)
    except:
        return "Unknown"
    return "Not Banned ✅" if period == 0 else "Banned ❌"

def check_ban_status(uid: str):
    """
    Check ban status for given UID
    
    Args:
        uid: User ID to check
        
    Returns:
        Dictionary containing ban status information
    """
    if not is_valid_uid(uid):
        return {
            "error": True,
            "message": "Invalid UID (must be 8-11 digits)",
            "status": "error"
        }
    
    try:
        # Make request to ban check API
        response = requests.get(
            BANCHECK_API_URL.format(uid=uid),
            headers=BANCHECK_HEADERS,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json().get("data", {})
            period = data.get("period", None)
            reason = data.get("reason") or data.get("desc") or ""
            is_banned = period != 0 if period is not None else False
            
            return {
                "error": False,
                "success": True,
                "uid": uid,
                "status": convert_ban_period_to_status(period),
                "status_code": "banned" if is_banned else "not_banned",
                "is_banned": is_banned,
                "period": period,
                "reason": reason,
                "timestamp": data.get("timestamp"),
                "raw_data": data
            }
        else:
            return {
                "error": True,
                "success": False,
                "message": f"API Error ({response.status_code})",
                "status": "api_error",
                "status_code": response.status_code
            }
            
    except requests.exceptions.Timeout:
        return {
            "error": True,
            "success": False,
            "message": "Request timeout",
            "status": "timeout"
        }
    except requests.exceptions.ConnectionError:
        return {
            "error": True,
            "success": False,
            "message": "Connection error",
            "status": "connection_error"
        }
    except Exception as e:
        return {
            "error": True,
            "success": False,
            "message": f"Request failed: {str(e)}",
            "status": "error"
        }

# ============================================
# API ENDPOINTS
# ============================================

@app.route('/')
def home():
    """Home endpoint with API information"""
    return jsonify({
        "status": "online",
        "service": "Free Fire Ban Check API",
        "endpoints": {
            "GET /check/<uid>": "Check ban status by UID",
            "GET /check?uid=<uid>": "Check ban status via query parameter",
            "POST /check": "Check ban status via POST request"
        },
        "usage": {
            "example_get": "https://your-domain.vercel.app/check/2919267964",
            "example_post": "POST to /check with JSON: {'uid': '2919267964'}"
        },
        "author": "Yash"
    })

@app.route('/check/<uid>', methods=['GET'])
def check_by_path(uid):
    """GET endpoint with UID in path"""
    result = check_ban_status(uid)
    return jsonify(result)

@app.route('/check', methods=['GET'])
def check_by_query():
    """GET endpoint with UID as query parameter"""
    uid = request.args.get('uid')
    
    if not uid:
        return jsonify({
            "error": True,
            "message": "UID parameter is required",
            "example": "/check?uid=2919267964"
        }), 400
    
    result = check_ban_status(uid)
    return jsonify(result)

@app.route('/check', methods=['POST'])
def check_by_post():
    """POST endpoint for checking ban status"""
    # Support both JSON and form-data
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
    
    result = check_ban_status(uid)
    return jsonify(result)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        "status": "healthy",
        "service": "bancheck-api",
        "timestamp": "Server time here"  # You can add datetime if needed
    })

@app.route('/batch', methods=['POST'])
def batch_check():
    """Batch check multiple UIDs (max 10)"""
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
    
    # Limit batch size
    if len(uids) > 10:
        return jsonify({
            "error": True,
            "message": "Maximum 10 UIDs allowed per batch"
        }), 400
    
    results = []
    for uid in uids:
        uid = str(uid).strip()
        result = check_ban_status(uid)
        results.append(result)
    
    return jsonify({
        "error": False,
        "count": len(results),
        "results": results
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": True,
        "message": "Endpoint not found",
        "available_endpoints": ["/", "/check", "/health", "/batch"]
    }), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({
        "error": True,
        "message": "Internal server error"
    }), 500

if __name__ == '__main__':
    app.run(debug=True)
