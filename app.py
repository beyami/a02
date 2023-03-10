from flask import Flask, request, render_template, redirect
import requests
import json
import random
from cs50 import SQL

app = Flask(__name__)

# Spotify APIの認証情報
client_id = ""
client_secret = ""
token_url = "https://accounts.spotify.com/api/token"
search_url = "https://api.spotify.com/v1/search"

# データベースを開く
db = SQL("sqlite:///votes.db")

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
        return render_template('index.html', genres=get_genres())

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

# 類似する音楽を表示するページ
@app.route('/experiment', methods=['POST'])
def experiment():
    # '/'から送信された'song_id'を用いて、audio_featuresを取得
    audio_features = get_audio_features(request.form.get('song_id'))
    # Spotifyからおすすめの音楽を取得
    recommendations = get_recommendations(audio_features=audio_features)['tracks']
    # おすすめされた音楽のidを保存するする変数の初期化
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

#現在受け入れている条件のリスト
SONG_TYPES = ('happy', 'sad', 'intense', 'calm')
# ランダム検索用のページ
@app.route("/random", methods=["POST"])
def random_page():
    if request.method =='POST':
        #どのような条件（明るい、悲しいなど）でランダム検索を行うかを取得
        song_type = request.form.get('song_type')
        #ランダム検索する楽曲の人気度
        popularity = request.form.get('popularity')
        #ランダム検索する楽曲のジャンル
        genre = request.form.get('genre')

        # おすすめの音楽を取得
        recommendations = get_recommendations(song_type=song_type, popularity=popularity, genre=genre)
        # ページを表示
        return render_template('random.html', recommendations=recommendations, song_type=song_type)

@app.route("/ranking", methods=['GET', 'POST'])
def ranking():
    # ランキング上位の曲に曲情報を追加する関数
    def add_song_info(songs):
        for song in songs:
            song.update(get_song_info(song['track_id']))
        return songs

    if request.method == 'GET':
        # 投票数上位10曲を取得し、曲情報を追加
        happy_songs = db.execute('SELECT * FROM votes WHERE song_type = ? LIMIT 10', 'happy')
        happy_songs = add_song_info(happy_songs)
        sad_songs = db.execute('SELECT * FROM votes WHERE song_type = ? LIMIT 10', 'sad')
        sad_songs = add_song_info(sad_songs)
        intense_songs = db.execute('SELECT * FROM votes WHERE song_type = ? LIMIT 10', 'intense')
        intense_songs = add_song_info(intense_songs)
        calm_songs = db.execute('SELECT * FROM votes WHERE song_type = ? LIMIT 10', 'calm')
        calm_songs = add_song_info(calm_songs)
        # ページの描画
        return render_template('ranking.html', happy_songs=happy_songs, sad_songs=sad_songs, intense_songs=intense_songs, calm_songs=calm_songs)

    elif request.method == 'POST':
        # フォームの入力内容を取得
        # 投票されたsong_idが不正だった場合、'/ranking'にリダイレクト
        # 英数字であれば、不正であっても影響は小さいので、チェックは簡易的です
        track_id = request.form.get("vote")
        if not track_id.isalnum():
            return redirect('/ranking')
        # song_typeが不正だった場合、投票を無効にして、'/ranking'にリダイレクト
        song_type = request.form.get("song_type")
        if song_type not in SONG_TYPES:
            return redirect('/ranking')
        # データベースを検索し、現在の投票数を取得
        result = db.execute("SELECT vote_count FROM votes WHERE track_id = ? AND song_type = ?", track_id, song_type)

        # 一度も投票されていない場合、カラムを作成
        if not result:
            db.execute("INSERT INTO votes VALUES(?, ?, 1)", track_id, song_type)
        # データベースのvote_countを1加算する
        else:
            vote_count = result[0]['vote_count']
            db.execute("UPDATE votes SET vote_count = ? WHERE track_id = ? AND song_type = ?", (vote_count + 1), track_id, song_type)
        return redirect('/ranking')

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

#現在利用できるジャンルを取得する関数
#ジャンルのリストが返り値です
def get_genres():
    url = 'https://api.spotify.com/v1/recommendations/available-genre-seeds'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['genres']
    else:
        return None

# Spotify API Recommendation パラメータ設定関数
# audio_featuresの値をターゲットの値に設定する
# keyは'acousticness'など
# gapとの和と差の範囲を最大値、最小値として設定する
def return_ranged_dict(audio_features, key, gap):
    targets = {}
    targets['target_' + key] = audio_features[key]

    # 値が0より小さい場合は0に設定
    # それ以外の場合はgapとaudio_featuresの差
    if audio_features[key] - gap > 0:
        targets['min_' + key] = audio_features[key] - gap
    else:
        targets['min_' + key] = 0

    # 上と同様の処理を最大値の設定にも行う
    if audio_features[key] - gap < 1:
        targets['max_' + key] = audio_features[key] + gap
    else:
        targets['min_' + key] = 1

    return targets


# 各種データをもとに、おすすめの音楽をSpotifyから取得する関数
# 引数にAudio_featuresを渡す場合
#    get_recommendations(audio_features=(audio_featuresの結果が格納されている変数など))
# 引数にsong_typeを渡す場合
#    get_recommendations(song_type=(SONG_TYPESの要素のうち一つ), (popularity=(1 ~ 100)), genre=(ジャンル名))
def get_recommendations(**kwargs):
    recommendations_url = 'https://api.spotify.com/v1/recommendations'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    # 検索条件を指定するための辞書
    targets = {
        'market':                   'JP',
        'limit':                    10,
    }

    # audio_featuresが渡されている場合に実行される文
    if kwargs.get('audio_features'):
        audio_features = kwargs.get('audio_features')
        # 検索パラメータ
        gap = 0.05
        targets = {
            'seed_tracks':              audio_features.get('id'),
            'target_key':               audio_features.get('key'),
            'target_mode':              audio_features.get('mode')
        }
        # min_, max_, target_ から始まる検索条件を一括指定
        targets.update(return_ranged_dict(audio_features, 'acousticness', gap))
        # targets.update(return_ranged_dict(audio_features, 'danceability', gap))
        targets.update(return_ranged_dict(audio_features, 'energy', gap))
        targets.update(return_ranged_dict(audio_features, 'instrumentalness', gap))
        targets.update(return_ranged_dict(audio_features, 'liveness', gap))

    # song_typeが渡されている場合に実行される文
    if kwargs.get('song_type'):
        song_type = kwargs.get('song_type')
        popularity = kwargs.get('popularity')
        genre = kwargs.get('genre')

        # エラー処理
        if song_type not in SONG_TYPES:
            # 不正な値の場合、デフォルト値を設定
            song_type = 'happy'

        if popularity.isdecimal():
            popularity = int(popularity)
        else:
            popularity = 100

        if not (0 <= popularity and popularity <= 100):
            popularity = 100

        if genre not in get_genres():
            genre = 'j-pop'

        # 人気度がキーワード引数として渡されていればそれを適用する
        if kwargs.get('popularity') != None:
            targets['target_popularity'] = kwargs.get('popularity')

        # 検索条件の設定
        targets['target_popularity'] = popularity
        targets['seed_genres'] = genre
        targets['limit'] = 5

        # 検索したい曲の特性によって、検索条件を変える
        if song_type == 'happy':
            # 0.75から1までの数値にランダムに設定
            targets['target_valence'] = random.randint(75, 100) / 100
        elif song_type == 'sad':
            # 0から0.25までの数値にランダムに設定
            targets['target_valence'] = random.randint(0, 25) / 100
        elif song_type == 'intense':
            targets['target_energy'] = random.randint(75, 100) / 100
        elif song_type == 'calm':
            targets['target_energy'] = random.randint(0, 25) / 100

    #エラー処理
    #'seed_tracks'または'seed_genres'が指定されていない場合検索が行えないため
    if not (targets.get('seed_tracks') or targets.get('seed_genres')):
        return None

    # GETリクエストでおすすめの楽曲を取得する
    response = requests.get(recommendations_url, params=targets, headers=headers)

    # JSON形式でレスポンスを取得し、楽曲情報をリストに格納する
    if response.status_code == 200:
        return response.json()
    else:
        return None

# idやそれに紐づいた名前を比較して、同じ曲じゃなければTrueを返す
def check_not_the_same(source_id, result_id):
    if source_id == result_id:
        return False
    elif get_song_info(source_id)['name'] == get_song_info(result_id)['name']:
        return False
    return True