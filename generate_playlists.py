# from sklearn.cluster import KMeans
import spotipy as sp
import pandas as pd

def cluster(user_id, selected_playlists):
    pass

def semantic(user_id, selected_playlists):
    pass

def artists(user_id, selected_playlists):
    pass

# Merge two or more playlists into one
# Adds only unique tracks so playlists with overlapping tracks aren't problematic
def merge(spotify, user_id, selected_playlists):
    # In case user only selected one playlist, don't do anything and return playlist id
    # To-do: Consider checking beforehand at option selection page
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

    new_name = "Merged " + " + ".join(names)

    return [make_playlist(spotify, user_id, new_name, uris)]

# Remove duplicate tracks from playlists
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

# Retrieve everything about each track in a playlist
# Includes name, artist, uri, and audio features
def get_track_features(spotify, user_id, playlist):
    pass

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