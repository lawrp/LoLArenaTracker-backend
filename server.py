from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os

app = Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": "https://lawrp.github.io"}})

API_KEY = os.getenv("RIOT_API_KEY")

def get_ddragon_version():
    try:
        version_url = "https://ddragon.leagueoflegends.com/api/versions.json"
        version_response = requests.get(version_url)
        version_data = version_response.json()
        return version_data[0]
    except Exception as e:
        print(f"Data Dragon version fetch error: {str(e)}")
        return "14.19.1"

DD_VERSION = get_ddragon_version()

@app.route('/api/login', methods=['POST'])
def login():
    if not API_KEY:
        return jsonify({'error': 'Riot API key not configured.'}), 500

    data = request.get_json()
    print(f"Received request data: {data}")
    riot_id = data.get('riotId') if data else None

    if not riot_id or '#' not in riot_id:
        print(f"Validation failed: riot_id={riot_id}")
        return jsonify({'error': 'Invalid Riot ID format. Use gameName#tagLine.'}), 400

    game_name, tag_line = riot_id.split('#')
    print(f"Parsed game_name: {game_name}, tag_line: {tag_line}")

    account_url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}?api_key={API_KEY}"
    try:
        account_response = requests.get(account_url)
        account_data = account_response.json()
        if account_response.status_code != 200:
            print(f"Account API error: {account_data}")
            return jsonify({'error': 'Invalid Riot ID or API error.', 'details': account_data}), 400
        puuid = account_data['puuid']
    except Exception as e:
        print(f"Account fetch error: {str(e)}")
        return jsonify({'error': 'Connection error during account fetch.'}), 500

    summoner_url = f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}?api_key={API_KEY}"
    try:
        summoner_response = requests.get(summoner_url)
        summoner_data = summoner_response.json()
        if summoner_response.status_code != 200:
            print(f"Summoner API error: {summoner_data}")
            return jsonify({'error': 'Summoner data not found.', 'details': summoner_data}), 400
        summoner_level = summoner_data['summonerLevel']
        profile_icon_id = summoner_data['profileIconId']
    except Exception as e:
        print(f"Summoner fetch error: {str(e)}")
        return jsonify({'error': 'Connection error during summoner fetch.'}), 500

    challenges_url = f"https://na1.api.riotgames.com/lol/challenges/v1/player-data/{puuid}?api_key={API_KEY}"
    try:
        challenge_response = requests.get(challenges_url)
        challenge_data = challenge_response.json()
        if challenge_response.status_code != 200:
            print(f"Challenge API error: {challenge_data}")
            return jsonify({'error': 'Challenge data fetch failed.', 'details': challenge_data}), 400
        print("Challenge Data:")
        print(json.dumps(challenge_data, indent=2))
    except Exception as e:
        print(f"Challenge fetch error: {str(e)}")
        return jsonify({'error': 'Connection error during challenge fetch.'}), 500

    return jsonify({
        'riotId': riot_id,
        'puuid': puuid,
        'summonerLevel': summoner_level,
        'profileIconId': profile_icon_id,
        'challengeData': challenge_data
    })

@app.route('/api/match-history/<puuid>', methods=['GET'])
def get_match_history(puuid):
    if not API_KEY:
        return jsonify({'error': 'Riot API key not configured.'}), 500

    match_url = f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=5&api_key={API_KEY}"
    try:
        match_response = requests.get(match_url)
        match_ids = match_response.json()
        if match_response.status_code != 200:
            return jsonify({'error': 'Failed to fetch match history.', 'details': match_ids}), 400

        matches = []
        for match_id in match_ids:
            match_detail_url = f"https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={API_KEY}"
            match_detail_response = requests.get(match_detail_url)
            match_detail = match_detail_response.json()
            if match_detail_response.status_code == 200:
                matches.append(match_detail)
    except Exception as e:
        return jsonify({'error': 'Connection error during match history fetch.'}), 500

    return jsonify(matches)

@app.route('/api/champions', methods=['GET'])
def get_champions():
    champions_url = f"https://ddragon.leagueoflegends.com/cdn/{DD_VERSION}/data/en_US/champion.json"
    try:
        champions_response = requests.get(champions_url)
        champions_data = champions_response.json()
        if champions_response.status_code != 200:
            print(f"Champions API error: {champions_data}")
            return jsonify({'error': 'Failed to fetch champions.', 'details': champions_data}), 400
        
        champion_list = [
            {
                'id': champ_id,
                'name': champ_data['name'],
                'image': f"https://ddragon.leagueoflegends.com/cdn/{DD_VERSION}/img/champion/{champ_data['image']['full']}"
            }
            for champ_id, champ_data in champions_data['data'].items()
        ]
        return jsonify(champion_list)
    except Exception as e:
        print(f"Champions fetch error: {str(e)}")
        return jsonify({'error': 'Connection error during champions fetch.'}), 500

@app.route('/api/challenges/config', methods=['GET'])
def get_challenge_config():
    if not API_KEY:
        return jsonify({'error': 'Riot API key not configured.'}), 500

    config_url = f"https://na1.api.riotgames.com/lol/challenges/v1/challenges/config?api_key={API_KEY}"
    try:
        config_response = requests.get(config_url)
        config_data = config_response.json()
        if config_response.status_code != 200:
            print(f"Challenge config API error: {config_data}")
            return jsonify({'error': 'Failed to fetch challenge config.', 'details': config_data}), 400
        print("Challenge Config:")
        print(json.dumps(config_data, indent=2))
        return jsonify(config_data)
    except Exception as e:
        print(f"Challenge config fetch error: {str(e)}")
        return jsonify({'error': 'Connection error during challenge config fetch.'}), 500

@app.route('/api/ddragon-version', methods=['GET'])
def get_ddragon_version():
    try:
        version_url = "https://ddragon.leagueoflegends.com/api/versions.json"
        version_response = requests.get(version_url)
        version_data = version_response.json()
        if version_response.status_code != 200:
            return jsonify({'error': 'Failed to fetch Data Dragon version.'}), 400
        latest_version = version_data[0]
        return jsonify({'version': latest_version})
    except Exception as e:
        print(f"Data Dragon version fetch error: {str(e)}")
        return jsonify({'error': 'Connection error during Data Dragon version fetch.'}), 500

if __name__ == '__main__':
    # Use the PORT environment variable provided by Render, default to 5000 for local development
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)