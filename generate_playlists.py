# from sklearn.cluster import KMeans
import spotipy as sp
import pandas as pd
import numpy as np

def cluster(selected_playlists):
    pass

def semantic(selected_playlists):
    pass

def artists(selected_playlists):
    pass

def merge(selected_playlists):
    pass

def remove_duplicates(selected_playlists):
    pass

def get_tracks(playlist_id):
    pass

def generate(option, selected_playlists):
    options = {
        "cluster": cluster,
        "semantic": semantic,
        "artists": artists,
        "merge": merge,
        "remove_duplicates": remove_duplicates
    }

    return options[option](selected_playlists)