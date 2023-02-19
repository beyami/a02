from flask import Flask, request, render_template
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Spotify API認証
# 環境変数の設定方法
# export SPOTIPY_CLIENT_ID="(あなたのSpotify Client ID)"
# export SPOTIPY_CLIENT_SECRET="(あなたのSpotify Client Secret)"
# 上記のコマンドをターミナルで実行する
client_credentials_manager = spotipy.oauth2.SpotifyClientCredentials()
spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

# 検索候補を表示するページ
@app.route('/suggest', methods=['POST'])
def suggest():

    # '/' のフォーム内容を取得
    song_name = str(request.form.get('song_name'))

    # '/' のフォーム内容が与えられていない場合の処理
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

    return render_template('suggest.html', songs=songs)