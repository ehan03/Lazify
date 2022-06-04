# from sklearn.cluster import KMeans
import spotipy as sp
import pandas as pd
import numpy as np

def cluster(user_id, selected_playlists):
    pass

def semantic(user_id, selected_playlists):
    pass

def artists(user_id, selected_playlists):
    pass

def merge(spotify, user_id, selected_playlists):
    # Get unique track uris
    tracks = list(set(get_track_uris(spotify, user_id, selected_playlists)))

    # Get names of selected playlists
    names = []
    for playlist in selected_playlists:
        names.append(spotify.user_playlist(user_id, playlist)['name'])

    # Create playlist
    new_name = "Merged " + " + ".join(names)

    # Work around so that returned object is iterable
    res = []
    res.append(make_playlist(spotify, user_id, new_name, tracks))
    return res


def remove_duplicates(user_id, selected_playlists):
    pass

# Retrieve only track uris for playlists
# To be used for merge and remove duplicates since audio features are not needed
def get_track_uris(spotify, user_id, playlists):
    # Get tracks from selected playlists
    tracks = []
    for playlist in playlists:
        results = spotify.user_playlist_tracks(user_id, playlist)
        tracks.extend(results['items'])

        while results['next']:
            results = spotify.next(results)
            tracks.extend(results['items'])
    
    # Get track uris
    uris = []
    for track in tracks:
        uris.append(track['track']['uri'])
    
    return uris

def make_playlist(spotify, user_id, name, tracks):
    # Create playlist
    playlist_id = spotify.user_playlist_create(user_id, name, public=False)['id']

    # Add tracks to playlist
    # 100 song limit per request
    offset = 0
    while offset < len(tracks):
        spotify.user_playlist_add_tracks(user_id, playlist_id, tracks[offset:offset+100])
        offset += 100

    return playlist_id

def generate(option, spotify, user_id, selected_playlists):
    options = {
        "cluster": cluster,
        "semantic": semantic,
        "artists": artists,
        "merge": merge,
        "remove_duplicates": remove_duplicates
    }

    return options[option](spotify, user_id, selected_playlists)



### To create a playlist from list of tracks
# user_playlist_create
# user_playlist_add_tracks