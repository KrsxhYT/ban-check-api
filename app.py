from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/checkban=<player_id>', methods=['GET'])
def check_banned(player_id):
    try:
        if not player_id:
            return jsonify({"error": "Player ID is required"}), 400

        # Step 1: Ban API
        garena_url = f"https://ff.garena.com/api/antihack/check_banned?lang=en&uid={player_id}"
        headers = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            'Accept': "application/json, text/plain, */*",
        }

        garena_response = requests.get(garena_url, headers=headers)
        if garena_response.status_code == 200:
            ban_data = garena_response.json()
        else:
            ban_data = {"data": {"is_banned": 0, "period": 0}}

        # Step 2: REGION API
        region_api_url = f"https://nr-codex-apis.onrender.com/REGION-API/check?uid={player_id}"
        region_response = requests.get(region_api_url)

        if region_response.status_code == 200:
            region_data = region_response.json()
        else:
            region_data = {}

        # Extract Data
        is_banned = ban_data.get('data', {}).get('is_banned', 0)
        period = ban_data.get('data', {}).get('period', 0)

        nickname = region_data.get('formatted_response', {}).get('nickname')
        region = region_data.get('formatted_response', {}).get('region')
        level = region_data.get('raw_api_response', {}).get('basicInfo', {}).get('level')

        response = {
            "player_id": player_id,
            "is_banned": bool(is_banned),
            "ban_period": period if is_banned else 0,
            "status": "BANNED" if is_banned else "NOT BANNED",
            "nickname": nickname,
            "region": region,
            "level": level,
            "credits": "API BY @KrsxhNvrDie"
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/check_key', methods=['GET'])
def check_key():
    return jsonify({
        "status": "no_key_required",
        "message": "This API does not require an API key"
    }), 200


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "Free Fire Ban Check API",
        "endpoints": {
            "check_ban": "/checkban=<uid>",
            "check_key": "/check_key"
        },
        "example": "https://krsxh-ban-check.vercel.app/checkban=123456789"
    }), 200
