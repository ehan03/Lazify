import os
import time
import spotipy as sp
import generate_playlists as gp
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect, render_template

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

@app.route("/")
@app.route("/index")
def index():
    """Render the home page.

    Render the home page. Users can login or check out the repository.

    Args:
        None
    
    Returns:
        A rendered template of index.html
    """

    return render_template("index.html")

@app.route("/login")
def login():
    """Login to Spotify.

    Login to Spotify with the OAuth flow and redirect to the callback.

    Args:
        None
    
    Returns:
        A redirect to the callback
    """

    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()

    return redirect(auth_url)

@app.route("/callback")
def callback():
    """Callback for Spotify OAuth.
    
    Callback for Spotify OAuth. Gets user's access token and stores it in session, then redirects to the
    playlist selection page.

    Args:
        None
    
    Returns:
        A redirect to the playlist selection page
    """

    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get("code")
    token_info = sp_oauth.get_access_token(code)
    session["token_info"] = token_info

    return redirect(url_for("playlists", _external=True))

@app.route("/playlists", methods=["GET", "POST"])
def playlists():
    """Render the playlist selection page.
    
    Render the playlist selection page with the user's playlists if the user is logged in. Here, the user
    can select which playlists(s) to modify or create new playlists from.

    Args:
        None
    
    Returns:
        A rendered template of playlists.html
    """

    # Make sure user is logged in
    try:
        token_info = get_token()
    except:
        return redirect(url_for("login"))
    
    if request.method == "GET":
        # Retrieve user info and user"s playlists
        spotify = sp.Spotify(auth=token_info["access_token"])
        user = spotify.current_user()
        display_name = user["display_name"]
        playlists = spotify.current_user_playlists()["items"]
        
        return render_template("playlists.html", display_name=display_name, playlists=playlists)
    
    return render_template("playlists.html")

@app.route("/select_option", methods=["GET", "POST"])
def select_option():
    """Render option selection page.
    
    Render the option selection page. The user's selected playlist(s) is/are stored in the session.
    On this page, the user can select which option to modify the playlist(s) with or generate
    new playlists from.

    Args:
        None
    
    Returns:
        A rendered template of select_option.html
    """

    # Make sure user is logged in
    try:
        get_token()
    except:
        return redirect(url_for("login"))

    if request.method == "GET":
        return render_template("select_option.html")
    else:
        # Retrieve ids of selected playlists
        selected_playlists = request.form.get("selected_playlists").split(",")
        session["selected_playlists"] = selected_playlists
        
        return render_template("select_option.html")

@app.route("/select_artist", methods=["GET", "POST"])
def select_artist():
    """Render artist selection page.
    
    If the user selected the "Artists" option, render the artist selection page. The user can select
    which artist(s) to create separate songs for.

    Args:
        None
    
    Returns:
        A rendered template of select_artist.html
    """

    # Make sure user is logged in
    try:
        token_info = get_token()
    except:
        return redirect(url_for("login"))
    
    if request.method == "POST":
        spotify = sp.Spotify(auth=token_info["access_token"])
        user_id = spotify.current_user()["id"]
        artists = sorted(gp.get_artists(spotify, user_id, session["selected_playlists"]))

        return render_template("select_artist.html", artists=artists)
    
    return render_template("select_artist.html")

@app.route("/result", methods=["GET", "POST"])
def result():
    """Render result page.
    
    Render the result page, which displays the new or modified playlist(s) using Spotify embeds.

    Args:
        None
    
    Returns:
        A rendered template of result.html
    """

    # Make sure user is logged in
    try:
        token_info = get_token()
    except:
        return redirect(url_for("login"))

    if request.method == "POST":
        new_playlist_ids = []
        spotify = sp.Spotify(auth=token_info["access_token"])
        user_id = spotify.current_user()["id"]

        # Check for each of the routes
        if "option" in request.form:
            option = request.form.get("option")
            new_playlist_ids = gp.generate(option, spotify, user_id, session["selected_playlists"])
        elif "selected_artists" in request.form:
            selected_artists = request.form.get("selected_artists").split(",")
            new_playlist_ids = gp.artists(spotify, user_id, selected_artists, session["selected_playlists"])

        sources = [f"https://open.spotify.com/embed/playlist/{new_playlist_id}?utm_source=generator&theme=0" for new_playlist_id in new_playlist_ids]

        return render_template("result.html", sources=sources)

def get_token():
    """Get the user's access token.
    
    Get the user's access token from the session or call the Spotify OAuth flow if the user has not
    authenticated yet. If the token has expired, refresh it. Return the token.

    Args:
        None
    
    Returns:
        The user's access token
    """

    token_info = session.get("token_info", None)
    if token_info is None:
        raise "No token found"

    # Check if token is expired and refresh if necessary
    now = int(time.time())
    is_expired = token_info["expires_at"] - now < 60
    if is_expired:
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info["refresh_token"])
    
    return token_info

def create_spotify_oauth():
    """Create a Spotify OAuth object.

    Create a Spotify OAuth object using the client ID and client secret.

    Args:
        None
    
    Returns:
        A Spotify OAuth object
    """

    # Parameters for OAuth
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    with app.app_context():
        redirect_uri = url_for("callback", _external=True)
    scope = os.getenv("SCOPE")

    sp_oauth = SpotifyOAuth(client_id, client_secret, redirect_uri, scope=scope)
    return sp_oauth