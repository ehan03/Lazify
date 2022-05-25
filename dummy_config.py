'''
Dummy configuration file for testing locally
Make sure to change client id, client secret, and secret key to your own
Rename this file to config.py
'''
class Config:
    # These can be found on your Spotify developer account dashboard after registering a new application
    # In general, don't share these with anyone
    CLIENT_ID = ""
    CLIENT_SECRET = ""

    # Scope for OAuth - don't change this
    SCOPE = "playlist-modify-public playlist-modify-private playlist-read-private"
    
    # Secret key for session management
    SECRET_KEY = ""