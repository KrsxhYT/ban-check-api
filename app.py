from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import time
from datetime import datetime, timedelta

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

def format_time_duration(seconds):
    """Format seconds into human readable duration"""
    if seconds <= 0:
        return "0 seconds"
    
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days > 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
    if secs > 0 and not parts:  # Only show seconds if no larger units
        parts.append(f"{secs} second{'s' if secs > 1 else ''}")
    elif secs > 0 and parts:
        parts.append(f"{secs} second{'s' if secs > 1 else ''}")
    
    return ", ".join(parts)

def parse_ban_data(ban_data):
    """Parse ban data and return comprehensive ban information"""
    period = ban_data.get("period", 0)
    reason = ban_data.get("reason") or ban_data.get("desc") or "No reason provided"
    ban_start = ban_data.get("ban_start") or ban_data.get("start_time")
    ban_end = ban_data.get("ban_end") or ban_data.get("end_time")
    
    # Check if banned
    is_banned = False
    ban_status = "Not Banned ✅"
    ban_type = "Not Banned"
    
    # If period is 0 or negative, might not be banned
    if period is None:
        period = 0
    
    # Try to determine ban status from multiple fields
    if period > 0:
        is_banned = True
    elif period == -1:
        is_banned = True
        ban_type = "Permanent"
    elif ban_start and ban_end:
        # Check if ban period is in the future
        try:
            start = datetime.fromtimestamp(ban_start) if isinstance(ban_start, (int, float)) else datetime.fromisoformat(str(ban_start).replace('Z', '+00:00'))
            end = datetime.fromtimestamp(ban_end) if isinstance(ban_end, (int, float)) else datetime.fromisoformat(str(ban_end).replace('Z', '+00:00'))
            now = datetime.now(start.tzinfo) if start.tzinfo else datetime.now()
            
            if now < end:
                is_banned = True
                # Calculate remaining seconds
                remaining = (end - now).total_seconds()
                period = int(remaining // 86400)  # Convert to days
        except:
            pass
    
    # Check ban status from response
    if ban_data.get("status") == "banned" or ban_data.get("is_banned") == True:
        is_banned = True
    
    # Additional check: if reason contains ban-related keywords
    if reason and any(keyword in reason.lower() for keyword in ['ban', 'hack', 'cheat', 'violation']):
        if not is_banned and period == 0:
            # Might be banned but period not set
            is_banned = True
            period = 1  # Default to 1 month if not specified
    
    if is_banned:
        if period == -1:
            ban_status = "Permanently Banned ❌"
            ban_type = "Permanent"
        elif period > 0:
            ban_status = f"Temporarily Banned ❌"
            ban_type = "Temporary"
        else:
            ban_status = "Banned ❌"
            ban_type = "Unknown"
    else:
        ban_status = "Not Banned ✅"
        ban_type = "Not Banned"
    
    # Calculate ban duration info
    ban_info = {
        "is_banned": is_banned,
        "ban_status": ban_status,
        "ban_type": ban_type,
        "period_days": period if period > 0 else 0,
        "reason": reason
    }
    
    # Try to get detailed timing info
    if is_banned and ban_start and ban_end:
        try:
            # Convert timestamps
            if isinstance(ban_start, (int, float)):
                start_dt = datetime.fromtimestamp(ban_start)
            else:
                start_dt = datetime.fromisoformat(str(ban_start).replace('Z', '+00:00')).replace(tzinfo=None)
            
            if isinstance(ban_end, (int, float)):
                end_dt = datetime.fromtimestamp(ban_end)
            else:
                end_dt = datetime.fromisoformat(str(ban_end).replace('Z', '+00:00')).replace(tzinfo=None)
            
            now = datetime.now()
            
            # Calculate since (time since ban started)
            since_seconds = int((now - start_dt).total_seconds())
            if since_seconds < 0:
                since_seconds = 0
            
            # Calculate remaining time
            remaining_seconds = int((end_dt - now).total_seconds())
            if remaining_seconds < 0:
                remaining_seconds = 0
            
            ban_info["since"] = format_time_duration(since_seconds)
            ban_info["unban_time"] = format_time_duration(remaining_seconds)
            ban_info["start_time"] = start_dt.strftime("%Y-%m-%d %H:%M:%S")
            ban_info["end_time"] = end_dt.strftime("%Y-%m-%d %H:%M:%S")
            
        except Exception as e:
            # If parsing fails, use period
            if period > 0:
                ban_info["since"] = "Unknown"
                ban_info["unban_time"] = f"{period} days"
            else:
                ban_info["since"] = "Unknown"
                ban_info["unban_time"] = "Unknown"
    else:
        # If no detailed timing available
        if is_banned and period > 0:
            ban_info["since"] = "Unknown"
            ban_info["unban_time"] = f"{period} days"
        elif is_banned and period == -1:
            ban_info["since"] = "Unknown"
            ban_info["unban_time"] = "Never (Permanent)"
        else:
            ban_info["since"] = "N/A"
            ban_info["unban_time"] = "N/A"
    
    return ban_info

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
        
        if res.status_code != 200:
            return {
                "error": True,
                "message": "Player ID not found"
            }
        
        player_data = res.json()
        
        # Check if player exists
        if not player_data.get('nickname'):
            return {
                "error": True,
                "message": "Player ID not found"
            }
        
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
        
        response_time = f"{round((time.time() - start_time) * 1000)}ms"
        
        if ban_response.status_code == 200:
            ban_data = ban_response.json().get("data", {})
            ban_info = parse_ban_data(ban_data)
            
            # Create formatted response
            result = {
                "success": True,
                "uid": uid,
                "nickname": nickname,
                "region": region,
                "level": level,
                "likes": likes,
                "ban_status": ban_info["ban_status"],
                "ban_type": ban_info["ban_type"],
                "period": f"{ban_info['period_days']} days" if ban_info['period_days'] > 0 else "0 days",
                "reason": ban_info["reason"],
                "since": ban_info["since"],
                "unban_time": ban_info["unban_time"],
                "start_time": ban_info.get("start_time", "N/A"),
                "end_time": ban_info.get("end_time", "N/A"),
                "response_time": response_time,
                "gif": "https://files.catbox.moe/lns4kb.gif" if ban_info["is_banned"] else "https://files.catbox.moe/7to40v.gif"
            }
            
            # Add box-drawing formatted representation
            if ban_info["is_banned"]:
                result["formatted"] = f"""
┌─ Bancheck Information
├─ UID: {uid}
├─ Username: {nickname}
├─ Region: {region}
├─ Level: {level}
├─ Likes: {likes}
├─ Status: {ban_info['ban_type']}
├─ Since: {ban_info['since']}
└─ Unban Time: {ban_info['unban_time']}
"""
            else:
                result["formatted"] = f"""
┌─ Player Information
├─ UID: {uid}
├─ Username: {nickname}
├─ Region: {region}
├─ Level: {level}
├─ Likes: {likes}
└─ Status: Not Banned ✅
"""
            
            return result
        else:
            # Still return player info even if ban check fails
            return {
                "success": True,
                "uid": uid,
                "nickname": nickname,
                "region": region,
                "level": level,
                "likes": likes,
                "ban_status": "Unknown",
                "ban_type": "Unknown",
                "period": "N/A",
                "reason": "Unable to retrieve ban status",
                "since": "N/A",
                "unban_time": "N/A",
                "response_time": response_time,
                "gif": "https://files.catbox.moe/7to40v.gif",
                "formatted": f"""
┌─ Player Information
├─ UID: {uid}
├─ Username: {nickname}
├─ Region: {region}
├─ Level: {level}
├─ Likes: {likes}
└─ Status: Unknown (Ban check failed)
"""
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
            "POST /check": "Get player info & ban status via POST",
            "POST /batch": "Check multiple UIDs (max 10)"
        },
        "response_fields": [
            "uid",
            "nickname",
            "region",
            "level",
            "likes",
            "ban_status",
            "ban_type",
            "period",
            "reason",
            "since",
            "unban_time",
            "response_time",
            "gif",
            "formatted"
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
        "version": "3.1.0"
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
