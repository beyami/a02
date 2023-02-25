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
