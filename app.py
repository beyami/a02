from flask import Flask, request, render_template
<<<<<<< HEAD
import requests
import json
=======
import spotipy

# Spotify API認証
# 環境変数の設定方法
# export SPOTIPY_CLIENT_ID="(あなたのSpotify Client ID)"
# export SPOTIPY_CLIENT_SECRET="(あなたのSpotify Client Secret)"
# 上記のコマンドをターミナルで実行する
client_credentials_manager = spotipy.oauth2.SpotifyClientCredentials()
spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
>>>>>>> 736455d0acb0046a054b2d26ce946aae9bc4647a

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
<<<<<<< HEAD
        song_name = request.form.get('song_name')

        # フォーム内容が与えられていない場合の処理
        if song_name is None:
            song_name = ''

        # 検索結果を取得
        songs = search_songs(song_name)
=======
        song_name = str(request.form.get('song_name'))

        # フォーム内容が与えられていない場合の処理
        if song_name == None:
            song_name = ''

        # Spotify API から曲名で検索
        search_results = spotify.search(q='track:' + song_name, limit=5, offset=0, type='track', market=None).get('tracks').get('items')

        # 検索結果を格納するための配列
        # 要素は辞書型です
        songs = []

        # 複数の検索結果それぞれに処理をする
        for search_result in search_results:
            # アーティストの名前が複数人いる場合に整形する処理
            # アーティストの名前を格納するための変数
            artist_name = ''
            counter = 0
            for artist in search_result.get('artists'):
                if counter == len(search_result.get('artists')) - 1:
                    artist_name += artist.get('name')
                else:
                    artist_name += artist.get('name') + ', '
                counter += 1

            # 検索結果を辞書型で格納
            songs.append({'name'    :search_result.get('name'),
                        'id'      :search_result.get('id'),
                        'artist'  :artist_name})
>>>>>>> 736455d0acb0046a054b2d26ce946aae9bc4647a

        return render_template('suggest.html', songs=songs)
    else:
        # GETならフォームを表示、検索内容取得
<<<<<<< HEAD
        return render_template('index.html')
=======
        return render_template('index.html')
>>>>>>> 736455d0acb0046a054b2d26ce946aae9bc4647a
