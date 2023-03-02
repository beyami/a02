from flask import Flask, request, render_template
import requests
import json

app = Flask(__name__)

# Spotify APIの認証情報
client_id = ""
client_secret = ""
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
    #入力がない場合、空白文字列の場合
    if not query or not query.strip():
        return []

    # 認証トークンを取得
    access_token = get_access_token()

    # GETリクエストで楽曲を検索する
    response = requests.get(search_url, params={
        'q': query,
        'type': 'track',
        'limit': 5,
        'market': 'JP'
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


#以下すべてプロトタイプ

# 各種データをもとに、おすすめの音楽をSpotifyから取得する関数
recommendations_url = 'https://api.spotify.com/v1/recommendations'
# Audio Featuresの結果を受け取り、それをもとにお勧めの音楽を取得する関数
def get_recommendations(audio_features):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    # 検索パラメータ
    targets = {
        'seed_tracks':              audio_features.get('id'),
        'market':                   'JP',
        'limit':                    10,
        'target_acousticness':      audio_features.get('acousticness'),
        'target_danceability':      audio_features.get('danceability'),
        'target_energy':            audio_features.get('energy'),
        'target_instrumentalness':  audio_features.get('instrumentalness'),
        'target_key':               audio_features.get('key'),
        'target_liveness':          audio_features.get('liveness'),
        'target_loudness':          audio_features.get('loudness'),
        'target_mode':              audio_features.get('mode'),
        'target_speechiness':       audio_features.get('speechiness'),
        'target_tempo':             audio_features.get('tempo'),
        'target_valence':           audio_features.get('valence')
    }


    # GETリクエストでおすすめの楽曲を取得する
    response = requests.get(recommendations_url, params=targets, headers={
        'Authorization': 'Bearer ' + access_token
    })

    # JSON形式でレスポンスを取得し、楽曲情報をリストに格納する
    response_data = response.json()
    return response_data

# idやそれに紐づいた名前を比較して、同じ曲じゃなければTrueを返す
def check_not_the_same(source_id, result_id):
    if source_id == result_id:
        return False
    elif get_song_info(source_id)['name'] == get_song_info(result_id)['name']:
        return False
    return True

# 類似する音楽を表示（実験的）
@app.route('/experiment', methods=['POST'])
def experiment():
    # '/'から送信された'song_id'を用いて、audio_featuresを取得
    audio_features = get_audio_features(request.form.get('song_id'))
    # Spotifyからおすすめの音楽を取得
    recommendations = get_recommendations(audio_features)['tracks']
    おすすめされた音楽のidを保存するする変数の初期化
    result_id = ""
    # 同じ曲がおすすめされた場合にそれを弾く処理
    for rec in recommendations:
        if check_not_the_same(request.form.get('song_id'), rec['id']):
            result_id = rec['id']
            break
    # ユーザーが検索に使った楽曲の情報を取得
    source_song_info = get_song_info(request.form.get('song_id'))
    # おすすめされた楽曲の情報を取得
    result_song_info = get_song_info(result_id)
    #'experiment.html'に各種情報を送信
    return render_template('experiment.html', source_song_info=source_song_info, result_song_info=result_song_info)