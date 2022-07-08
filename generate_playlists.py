import os

# Work around for Fortran and Ctrl+C handling
os.environ["FOR_DISABLE_CONSOLE_CTRL_HANDLER"] = "1"

import spotipy as sp
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_similarity

def cluster(spotify, user_id, selected_playlists):
    """Groups tracks into clusters based on audio features using K-means.
    
    Retrieves tracks from selected playlists and their relevant audio features, performs PCA on the features,
    and then clusters the features using K-means into optimal number of clusters based on silhouette score.

    Args:
        spotify (spotipy.Spotify): Spotify API object
        user_id (str): Spotify user id
        selected_playlists (list): List of ids for the selected playlists
    
    Returns:
        list: List of ids for the newly created playlists     
    """

    data = pd.DataFrame()
    for playlist in selected_playlists:
        df = get_track_features(spotify, user_id, playlist)[["uri", "acousticness", "danceability", "energy", "instrumentalness", "liveness", "loudness", "speechiness", "valence"]]
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
    selected_playlists_names = [spotify.user_playlist(user_id, playlist)["name"] for playlist in selected_playlists]
    new_playlist_ids = []
    for i in range(n_clusters):
        uris = data[data["cluster"] == i]["uri"].tolist()
        name = "[Lazify] Cluster #" + str(i + 1) + ": " + " + ".join(selected_playlists_names)
        new_playlist_ids.append(make_playlist(spotify, user_id, name, uris))
    
    return new_playlist_ids

def recommend(spotify, user_id, selected_playlists):
    """Create a playlist of recommended tracks based on the selected playlists.

    Retrieve recommended tracks from the Spotify API, using the tracks in the selected playlists as seed tracks,
    and then create a new playlist with the top 25 tracks with the highest cosine similarity to the seed tracks.
    The number of similarity scores relies on the number of seed tracks, so if there are less than 25 seed tracks,
    just randomly select 25 tracks from the recommended tracks.

    Args:
        spotify (spotipy.Spotify): Spotify API object
        user_id (str): Spotify user id
        selected_playlists (list): List of ids for the selected playlists
    
    Returns:
        list: List containing the id for the newly created playlist, to bypass iteration in app.py
    """
    
    playlist_names = []
    data = pd.DataFrame()
    for playlist in selected_playlists:
        playlist_names.append(spotify.user_playlist(user_id, playlist)["name"])
        df = get_track_features(spotify, user_id, playlist)[["uri", "acousticness", "danceability", "energy", "instrumentalness", "liveness", "loudness", "speechiness", "valence"]]
        data = data.append(df)
    data = data.drop_duplicates()
    new_name = "[Lazify] Recommended: " + " + ".join(playlist_names)

    # Track info for recommended tracks
    seeds = data["uri"].tolist()
    offset = 0
    uris = []
    while offset < len(data):
        results = spotify.recommendations(seed_tracks=seeds[offset:offset+5], limit=25)
        tracks = results["tracks"]
        for track in tracks:
            uris.append(track["uri"])
        offset += 5
    
    # Audio features for recommended tracks
    offset = 0
    all_features = []
    acousticness, danceability, energy, instrumentalness, liveness, loudness, speechiness, valence = [], [], [], [], [], [], [], []

    while offset < len(uris):
        all_features += spotify.audio_features(uris[offset:offset+100])
        offset += 100
    
    for features in all_features:
        acousticness.append(features["acousticness"])
        danceability.append(features["danceability"])
        energy.append(features["energy"])
        instrumentalness.append(features["instrumentalness"])
        liveness.append(features["liveness"])
        loudness.append(features["loudness"])
        speechiness.append(features["speechiness"])
        valence.append(features["valence"])

    # Combine everything
    rec = {
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
    
    # Make recommendations dataframe, removing duplicates and any tracks that were in the seed tracks
    recommendations = pd.DataFrame(rec)
    recommendations = recommendations.drop_duplicates()
    recommendations = recommendations[~recommendations["uri"].isin(data["uri"])]
    recommendations = recommendations.reset_index(drop=True)

    # Randomly select 25 tracks from the recommendations dataframe if there were less than 25 seed tracks
    if len(seeds) < 25:
        recommendations = recommendations.sample(n=25)
        return [make_playlist(spotify, user_id, new_name, recommendations["uri"].tolist())]

    # Calculate cosine similarity scores for each track otherwise
    scaler = MinMaxScaler()
    seed_features_scaled = scaler.fit_transform(data.iloc[:, 1:])
    recommendations_scaled = scaler.transform(recommendations.iloc[:, 1:])
    cosine_similarity_scores = cosine_similarity(seed_features_scaled, recommendations_scaled)
    final_recommendations = recommendations.loc[[np.argmax(i) for i in cosine_similarity_scores]]
    final_recommendations = final_recommendations.head(25)

    return [make_playlist(spotify, user_id, new_name, final_recommendations["uri"].tolist())]
    
def artists(spotify, user_id, selected_artists, selected_playlists):
    """Separates tracks of the selected playlists by the selected artists.

    Retrieves tracks from selected playlists and their artist, separates tracks by the selected artists,
    and then creates new playlists for each artist or adds tracks to existing playlists.

    Args:
        spotify (spotipy.Spotify): Spotify API object
        user_id (str): Spotify user id
        selected_artists (list): List of ids for the selected artists to separate tracks by
        selected_playlists (list): List of ids for the selected playlists
    
    Returns:
        list: List of ids for the newly created or existing playlists
    """

    data = pd.DataFrame()
    for playlist in selected_playlists:
        df = get_track_features(spotify, user_id, playlist)[["uri", "artist"]]
        data = data.append(df)
    data = data.drop_duplicates()

    # Get user"s current playlists
    current_playlists = spotify.current_user_playlists()["items"]
    current_playlist_ids = [playlist["id"] for playlist in current_playlists]
    current_playlist_names = [playlist["name"] for playlist in current_playlists]

    # Make the playlist(s)
    new_playlist_ids = []
    for artist in selected_artists:
        uris = data[data["artist"] == artist]["uri"].tolist()
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

def merge(spotify, user_id, selected_playlists):
    """Merges two or more playlists into one.

    Creates a new playlist with all of the unique tracks from the selected playlists.

    Args:
        spotify (spotipy.Spotify): Spotify API object
        user_id (str): Spotify user id
        selected_playlists (list): List of ids for the selected playlists
    
    Returns:
        list: List containing the id for the newly created playlist, to bypass iteration in app.py
    """

    # In case user only selected one playlist, don"t do anything and return playlist id
    # To-do: Consider checking number of selected playlists at option selection page to avoid this
    if len(selected_playlists) == 1:
        return selected_playlists

    uris, names = [], []
    for playlist in selected_playlists:
        uris.extend(get_track_uris(spotify, user_id, playlist))
        names.append(spotify.user_playlist(user_id, playlist)["name"])
    
    uris = list(set(uris))
    new_name = "[Lazify] Merged: " + " + ".join(names)

    return [make_playlist(spotify, user_id, new_name, uris)]

# To-do: Only accounts for identical uris, might be problematic if identical tracks were released as single and in album
def remove_duplicates(spotify, user_id, selected_playlists):
    """Removes duplicate tracks from playlists.

    Removes any duplicate tracks from each of the selected playlists, modifying them in place.

    Args:
        spotify (spotipy.Spotify): Spotify API object
        user_id (str): Spotify user id
        selected_playlists (list): List of ids for the selected playlists
    
    Returns:
        list: List of ids for the modified playlists
    """
    
    for playlist in selected_playlists:
        uris = get_track_uris(spotify, user_id, playlist)
        unique_uris = list(set(uris))

        # Skip playlists that don"t contain duplicates
        if len(unique_uris) == len(uris):
            continue
        
        spotify.user_playlist_replace_tracks(user_id, playlist, unique_uris)

    return selected_playlists

def get_track_uris(spotify, user_id, playlist):
    """Retrieves track uris for a playlist.

    Retrieves only track uris for a playlist, not including the track"s audio features, which will be
    more efficient than get_track_features for large playlists.

    Args:
        spotify (spotipy.Spotify): Spotify API object
        user_id (str): Spotify user id
        playlist (str): Id for the playlist
    
    Returns:
        list: List of track uris
    """

    results = spotify.user_playlist_tracks(user_id, playlist)
    tracks = results["items"]
    uris = []

    while results["next"]:
        results = spotify.next(results)
        tracks.extend(results["items"])
    
    for track in tracks:
        uris.append(track["track"]["uri"])

    return uris

def get_artists(spotify, user_id, selected_playlists):
    """Retrieves unique artists from playlists.
    
    Retrieves every distinct artist from all of the tracks in the selected playlists.

    Args:
        spotify (spotipy.Spotify): Spotify API object
        user_id (str): Spotify user id
        selected_playlists (list): List of ids for the selected playlists
    
    Returns:
        list: List of unique artists
    """

    artists = []
    for playlist in selected_playlists:
        results = spotify.user_playlist_tracks(user_id, playlist)
        tracks = results["items"]
        while results["next"]:
            results = spotify.next(results)
            tracks.extend(results["items"])
        
        for track in tracks:
            artists.append(track["track"]["artists"][0]["name"])

    return list(set(artists))

def get_track_features(spotify, user_id, playlist):
    """Retrieves all information about tracks in a playlist.

    Retrieves all information about tracks in a playlist, including the track"s audio features.

    Args:
        spotify (spotipy.Spotify): Spotify API object
        user_id (str): Spotify user id
        playlist (str): Id for the playlist
    
    Returns:
        pandas.DataFrame: DataFrame containing all track information
    """

    # Track info
    results = spotify.user_playlist_tracks(user_id, playlist)
    tracks = results["items"]
    names, artists, uris = [], [], []

    while results["next"]:
        results = spotify.next(results)
        tracks.extend(results["items"])
    
    for track in tracks:
        names.append(track["track"]["name"])
        artists.append(track["track"]["artists"][0]["name"])
        uris.append(track["track"]["uri"])

    # Audio features
    offset = 0
    all_features = []
    acousticness, danceability, energy, instrumentalness, liveness, loudness, speechiness, valence = [], [], [], [], [], [], [], []

    while offset < len(uris):
        all_features += spotify.audio_features(uris[offset:offset+100])
        offset += 100
    
    for features in all_features:
        acousticness.append(features["acousticness"])
        danceability.append(features["danceability"])
        energy.append(features["energy"])
        instrumentalness.append(features["instrumentalness"])
        liveness.append(features["liveness"])
        loudness.append(features["loudness"])
        speechiness.append(features["speechiness"])
        valence.append(features["valence"])

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

def make_playlist(spotify, user_id, name, uris):
    """Creates a new playlist.
    
    Creates a new playlist with the given name and adds the given tracks to it.

    Args:
        spotify (spotipy.Spotify): Spotify API object
        user_id (str): Spotify user id
        name (str): Name for the new playlist
        uris (list): List of track uris
    
    Returns:
        str: Id for the new playlist
    """

    playlist_id = spotify.user_playlist_create(user_id, name, public=False)["id"]

    offset = 0
    while offset < len(uris):
        spotify.user_playlist_add_tracks(user_id, playlist_id, uris[offset:offset+100])
        offset += 100

    return playlist_id

def generate(option, spotify, user_id, selected_playlists):
    """Generates a playlist or playlists based on the selected option.

    Calls the appropriate function based on the selected option for the user and their selected playlists,
    and returns the id(s) for the generated playlist(s).

    Args:
        option (str): Selected option
        spotify (spotipy.Spotify): Spotify API object
        user_id (str): Spotify user id
        selected_playlists (list): List of ids for the selected playlists
    
    Returns:
        list: List of id(s) for the generated playlist(s)
    """

    options = {
        "cluster": cluster,
        "recommend": recommend,
        "merge": merge,
        "remove_duplicates": remove_duplicates
    }

    return options[option](spotify, user_id, selected_playlists)