# from sklearn.cluster import KMeans
import spotipy as sp
import pandas as pd

'''
Main functions used to generate playlists
Also handles retrieving track information
'''
def cluster(user_id, selected_playlists):
    pass

def semantic(user_id, selected_playlists):
    pass

def artists(spotify, user_id, artist, selected_playlists):
    pass

# Merge two or more playlists into one
# Adds only unique tracks so playlists with overlapping tracks aren't problematic
def merge(spotify, user_id, selected_playlists):
    # In case user only selected one playlist, don't do anything and return playlist id
    # To-do: Consider checking number of selected playlists at option selection page to avoid this
    if len(selected_playlists) == 1:
        return selected_playlists

    # Get unique track uris
    uris = []
    for playlist in selected_playlists:
        uris.extend(get_track_uris(spotify, user_id, playlist))
    
    uris = list(set(uris))

    # Get names of selected playlists
    names = []
    for playlist in selected_playlists:
        names.append(spotify.user_playlist(user_id, playlist)['name'])

    new_name = "[Lazify] Merged " + " + ".join(names)

    return [make_playlist(spotify, user_id, new_name, uris)]

# Remove duplicate tracks from playlists
# To-do: Only accounts for identical uris, might be problematic if identical tracks were released as single and in album
def remove_duplicates(spotify, user_id, selected_playlists):
    for playlist in selected_playlists:
        uris = get_track_uris(spotify, user_id, playlist)
        unique_uris = list(set(uris))

        # Skip playlists that don't contain duplicates
        if len(unique_uris) == len(uris):
            continue
        
        # Modify playlist in place
        spotify.user_playlist_replace_tracks(user_id, playlist, unique_uris)

    return selected_playlists

# Retrieve only track uris for playlists
# To be used for merge and remove duplicates since audio features aren't needed
def get_track_uris(spotify, user_id, playlist):
    results = spotify.user_playlist_tracks(user_id, playlist)
    tracks = results['items']
    uris = []

    while results['next']:
        results = spotify.next(results)
        tracks.extend(results['items'])
    
    for track in tracks:
        uris.append(track['track']['uri'])

    return uris

# Retrieve unique artists from playlists
def get_artists(spotify, user_id, selected_playlists):
    artists = []
    for playlist in selected_playlists:
        results = spotify.user_playlist_tracks(user_id, playlist)
        tracks = results['items']
        while results['next']:
            results = spotify.next(results)
            tracks.extend(results['items'])
        
        for track in tracks:
            artists.append(track['track']['artists'][0]['name'])

    return list(set(artists))

# Retrieve everything about each track in a playlist
# Includes name, artist, uri, and relevant audio features
def get_track_features(spotify, user_id, playlist):
    # Track info
    results = spotify.user_playlist_tracks(user_id, playlist)
    tracks = results['items']
    names, artists, uris = [], [], []

    while results['next']:
        results = spotify.next(results)
        tracks.extend(results['items'])
    
    for track in tracks:
        names.append(track['track']['name'])
        artists.append(track['track']['artists'][0]['name'])
        uris.append(track['track']['uri'])

    # Audio features
    offset = 0
    all_features = []
    acousticness, danceability, energy, instrumentalness, liveness, loudness, speechiness, valence = [], [], [], [], [], [], [], []
    
    while offset < len(uris):
        all_features = spotify.audio_features(uris[offset:offset+100])
        offset += 100
    
    for features in all_features:
        acousticness.append(features['acousticness'])
        danceability.append(features['danceability'])
        energy.append(features['energy'])
        instrumentalness.append(features['instrumentalness'])
        liveness.append(features['liveness'])
        loudness.append(features['loudness'])
        speechiness.append(features['speechiness'])
        valence.append(features['valence'])

    # Combine everything
    data = {
            "name": names, 
            "artist": artists, 
            "uri": uris,
            "acousticness": acousticness,
            "danceability": danceability,
            "energy": energy,
            "instrumentalness": instrumentalness,
            "liveness": liveness,
            "loudness": loudness,
            "speechiness": speechiness,
            "valence": valence
        }
    
    df = pd.DataFrame(data)
    return df

# Create playlist given a name and a list of track uris
def make_playlist(spotify, user_id, name, uris):
    playlist_id = spotify.user_playlist_create(user_id, name, public=False)['id']

    offset = 0
    while offset < len(uris):
        spotify.user_playlist_add_tracks(user_id, playlist_id, uris[offset:offset+100])
        offset += 100

    return playlist_id

# Main driver
def generate(option, spotify, user_id, selected_playlists):
    options = {
        "cluster": cluster,
        "semantic": semantic,
        "artists": artists,
        "merge": merge,
        "remove_duplicates": remove_duplicates
    }

    return options[option](spotify, user_id, selected_playlists)