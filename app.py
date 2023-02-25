from flask import Flask, request, render_template
import requests
import json

app = Flask(__name__)

# Spotify APIの認証情報
client_id = "YOUR_ID"
client_secret = "YOUR_SECRET"
token_url = "https://accounts.spotify.com/api/token"
search_url = "https://api.spotify.com/v1/search"

# 認証トークンを取得する関数
def get_access_token():
    # POSTリクエストで認証トークンを取得する
    auth_response = requests.post(token_url, {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
    })

    # JSON形式でレスポンスを取得し、トークンを返す
    auth_response_data = auth_response.json()
    return auth_response_data['access_token']

# 楽曲検索を行う関数
def search_songs(query):
    # 認証トークンを取得
    access_token = get_access_token()

    # GETリクエストで楽曲を検索する
    response = requests.get(search_url, params={
        'q': query,
        'type': 'track',
        'limit': 5,
    }, headers={
        'Authorization': 'Bearer ' + access_token
    })

    # JSON形式でレスポンスを取得し、楽曲情報をリストに格納する
    response_data = response.json()
    songs = []
    for track in response_data['tracks']['items']:
        artists = ", ".join([artist['name'] for artist in track['artists']])
        songs.append({
            'name': track['name'],
            'id': track['id'],
            'artist': artists,
        })

    return songs

access_token = get_access_token()

# トップページ
@app.route("/", methods=["GET", "POST"])
def search():
    # "POST"なら検索結果表示
    if request.method == "POST":
        # フォーム内容取得
        song_name = request.form.get('song_name')

        # フォーム内容が与えられていない場合の処理
        if song_name is None:
            song_name = ''

        # 検索結果を取得
        songs = search_songs(song_name)

        return render_template('suggest.html', songs=songs)
    else:
        # GETならフォームを表示、検索内容取得
        return render_template('index.html')

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