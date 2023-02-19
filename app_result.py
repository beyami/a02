from flask import Flask, render_template, request
import requests
import json

app = Flask(__name__)

# Spotifyのアクセストークンを取得するための情報
CLIENT_ID = 'your_id'
CLIENT_SECRET = 'your_secret'
AUTH_URL = 'https://accounts.spotify.com/api/token'
SCOPE = 'user-library-read'
REDIRECT_URI = 'http://localhost:5000/callback'

# アクセストークンを取得するための関数
def get_access_token():
    payload = {
        'grant_type': 'client_credentials',
    }
    response = requests.post(
        AUTH_URL,
        auth=(CLIENT_ID, CLIENT_SECRET),
        data=payload,
    )
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        return None

# 初期化時にアクセストークンを取得しておく
access_token = get_access_token()

#resultに関するページなど
@app.route('/result', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        song_id = request.form['song_id']
        song_info = get_song_info(song_id)

        #ジャンルが複数ある場合にカンマ区切りで格納する
        genres_str = ", ".join(song_info['genres'])
        song_info['genres'] = genres_str
        return render_template('result.html', song_info=song_info)
    return render_template('result.html')

#アーティストのジャンルを取得
def get_artist_genres(artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}"
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        artist_info = json.loads(response.text)
        genres = artist_info.get('genres', [])
        return genres
    else:
        return []

#楽曲の情報の取得
def get_song_info(song_id):
    url = f"https://api.spotify.com/v1/tracks/{song_id}"
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        song_info = json.loads(response.text)
        # アーティスト情報からジャンル情報を取得して曲情報に追加する
        artist_id = song_info.get('artists', [{}])[0].get('id', '')
        genres = get_artist_genres(artist_id)
        song_info['genres'] = genres
        # オーディオフィーチャー情報を取得して曲情報に追加する
        audio_features = get_audio_features(song_id)
        if audio_features:
            song_info['audio_features'] = audio_features
        return song_info
    else:
        return None

#オーディオフィーチャーの取得
def get_audio_features(song_id):
    url = f"https://api.spotify.com/v1/audio-features/{song_id}"
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        audio_features = json.loads(response.text)
        return audio_features
    else:
        return None

if __name__ == '__main__':
    app.run(debug=True)
