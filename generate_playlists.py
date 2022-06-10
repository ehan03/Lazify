import os

# Work around for Fortran and Ctrl+C handling
os.environ['FOR_DISABLE_CONSOLE_CTRL_HANDLER'] = '1'

from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import spotipy as sp
import pandas as pd
import numpy as np

'''
Main functions used to generate playlists
Also handles retrieving track information
'''
# Cluster tracks of the selected playlists by audio features
def cluster(spotify, user_id, selected_playlists):
    data = pd.DataFrame()
    for playlist in selected_playlists:
        df = get_track_features(spotify, user_id, playlist)[['uri', 'acousticness', 'danceability', 'energy', 'instrumentalness', 'liveness', 'loudness', 'speechiness', 'valence']]
        data = data.append(df)
    data = data.drop_duplicates()

    # Normalize audio feature data
    scaler = MinMaxScaler()
    data_std = scaler.fit_transform(data.iloc[:, 1:])

    # PCA
    # Arbitrarily chose 0.8 as cutoff for explained variance
    pca = PCA(n_components=0.8)
    reduced = pca.fit_transform(data_std)

    # Find optimal number of clusters using silhouette score
    # Arbitrarily chose 20 as max number of clusters
    N_MAX = 20
    silhouette_scores = []
    for i in range(2, N_MAX + 1):
        clusterer = KMeans(n_clusters=i, init="k-means++", random_state=1738)
        cluster_labels = clusterer.fit_predict(reduced)
        silhouette_scores.append(silhouette_score(reduced, cluster_labels))
    n_clusters = np.argmax(silhouette_scores) + 2

    # Cluster
    kmeans = KMeans(n_clusters=n_clusters, init="k-means++", random_state=1738)
    cluster_labels = kmeans.fit_predict(reduced)
    data["cluster"] = cluster_labels

    # Make new playlists
    selected_playlists_names = [spotify.user_playlist(user_id, playlist)['name'] for playlist in selected_playlists]
    new_playlist_ids = []
    for i in range(n_clusters):
        uris = data[data['cluster'] == i]['uri'].tolist()
        name = "[Lazify] Cluster #" + str(i + 1) + ": " + " + ".join(selected_playlists_names)
        new_playlist_ids.append(make_playlist(spotify, user_id, name, uris))
    
    return new_playlist_ids

# Cluster tracks of the selected playlists by title based on semantic similarity
def semantic(spotify, user_id, selected_playlists):
    data = pd.DataFrame()
    for playlist in selected_playlists:
        df = get_track_features(spotify, user_id, playlist)[['uri', 'name']]
        data = data.append(df)
    data = data.drop_duplicates()

    # To-do

# Separate tracks of the selected playlists by the selected artists
def artists(spotify, user_id, selected_artists, selected_playlists):
    data = pd.DataFrame()
    for playlist in selected_playlists:
        df = get_track_features(spotify, user_id, playlist)[['uri', 'artist']]
        data = data.append(df)
    data = data.drop_duplicates()

    # Get user's current playlists
    current_playlists = spotify.current_user_playlists()['items']
    current_playlist_ids = [playlist['id'] for playlist in current_playlists]
    current_playlist_names = [playlist['name'] for playlist in current_playlists]

    # Make the playlist(s)
    new_playlist_ids = []
    for artist in selected_artists:
        uris = data[data['artist'] == artist]['uri'].tolist()
        name = "[Lazify] Artist: " + artist

        # Check if playlist for that artist already exists
        if name in current_playlist_names:
            index = current_playlist_names.index(name)
            new_playlist_ids.append(current_playlist_ids[index])

            offset = 0
            while offset < len(uris):
                spotify.user_playlist_add_tracks(user_id, current_playlist_ids[index], uris[offset:offset+100])
                offset += 100

        # If not, make a new playlist
        else:
            new_playlist_ids.append(make_playlist(spotify, user_id, name, uris))
    
    return remove_duplicates(spotify, user_id, new_playlist_ids)

# Merge two or more playlists into one
# Adds only unique tracks so playlists with overlapping tracks aren't problematic
def merge(spotify, user_id, selected_playlists):
    # In case user only selected one playlist, don't do anything and return playlist id
    # To-do: Consider checking number of selected playlists at option selection page to avoid this
    if len(selected_playlists) == 1:
        return selected_playlists

    uris, names = [], []
    for playlist in selected_playlists:
        uris.extend(get_track_uris(spotify, user_id, playlist))
        names.append(spotify.user_playlist(user_id, playlist)['name'])
    
    uris = list(set(uris))
    new_name = "[Lazify] Merged: " + " + ".join(names)

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
        all_features += spotify.audio_features(uris[offset:offset+100])
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
        "merge": merge,
        "remove_duplicates": remove_duplicates
    }

    return options[option](spotify, user_id, selected_playlists)