import time
import generate_playlists as gp
import spotipy as sp
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect, render_template
from config import Config

app = Flask(__name__)
app.config.from_object(Config)


'''
Routes
'''
# Home page where users log in
@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html")

# Redirect to Spotify for authorization
@app.route('/login')
def login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()

    return redirect(auth_url)

# Authorization callback
@app.route('/callback')
def callback():
    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info

    return redirect(url_for('playlists', _external=True))

# Display user's playlists
@app.route('/playlists', methods=['GET', 'POST'])
def playlists():
    # Make sure user is logged in
    try:
        token_info = get_token()
    except:
        return redirect(url_for('login'))
    
    if request.method == 'GET':
        # Retrieve user info and user's playlists
        spotify = sp.Spotify(auth=token_info['access_token'])
        user = spotify.current_user()
        display_name = user['display_name']
        playlists = spotify.current_user_playlists()['items']
        
        return render_template("playlists.html", display_name=display_name, playlists=playlists)
    
    return render_template("playlists.html")

# Playlist generation options
@app.route('/select_option', methods=['GET', 'POST'])
def select_option():
    # Make sure user is logged in
    try:
        get_token()
    except:
        return redirect(url_for('login'))

    if request.method == 'GET':
        return render_template("select_option.html")
    else:
        # Retrieve ids of selected playlists
        selected_playlists = request.form.get('selected_playlists').split(',')
        session['selected_playlists'] = selected_playlists
        
        return render_template("select_option.html")

# Generate playlist(s) and display them
@app.route('/result', methods=['GET', 'POST'])
def result():
    # Make sure user is logged in
    try:
        token_info = get_token()
    except:
        return redirect(url_for('login'))

    if request.method == 'GET':
        return render_template("result.html")
    else:
        # Retrieve selected option
        option = request.form.get('option')
        
        # Generate playlist(s) based on selected option
        new_playlists = gp.generate(option, session['selected_playlists'])

        return ""


'''
Helper functions for authorization and token management
'''
def get_token():
    token_info = session.get('token_info', None)
    if token_info is None:
        raise "No token found"

    # Check if token is expired and refresh if necessary
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60
    if is_expired:
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    
    return token_info

def create_spotify_oauth():
    # Parameters for OAuth
    client_id = app.config['CLIENT_ID']
    client_secret = app.config['CLIENT_SECRET']
    with app.app_context():
        redirect_uri = url_for('callback', _external=True)
    scope = app.config['SCOPE']

    sp_oauth = SpotifyOAuth(client_id, client_secret, redirect_uri, scope=scope)
    return sp_oauth