def get_api_key():
    """Retrieve the YouTube API key from environment variables."""
    import os
    return os.getenv('YOUTUBE_API_KEY')

def get_oauth_token():
    """Retrieve the OAuth token from environment variables."""
    import os
    return os.getenv('YOUTUBE_OAUTH_TOKEN')

def authenticate():
    """Authenticate the user and return the credentials."""
    from google.oauth2.credentials import Credentials
    token = get_oauth_token()
    if token:
        return Credentials.from_authorized_user_info(token)
    else:
        raise ValueError("OAuth token not found. Please set the YOUTUBE_OAUTH_TOKEN environment variable.")