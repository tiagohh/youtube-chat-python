import os

class YouTubeClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.service = self.authenticate()

    def authenticate(self):
        from googleapiclient.discovery import build
        return build('youtube', 'v3', developerKey=self.api_key)

    def connect(self):
        """Return True if the underlying service object was created."""
        return self.service is not None

    def get_live_chat_id(self, video_id, cache_file=None):
        """Return the live chat ID for a video, optionally caching it.

        If ``cache_file`` is provided and the file exists the ID is read from
        disk.  Otherwise the API is called and the result is written to the
        cache file (if one was given).
        """
        if cache_file and os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    return f.read().strip()
            except Exception:
                pass
        request = self.service.videos().list(part='liveStreamingDetails', id=video_id)
        response = request.execute()
        live_chat_id = response['items'][0]['liveStreamingDetails']['activeLiveChatId']
        if cache_file:
            try:
                with open(cache_file, 'w') as f:
                    f.write(live_chat_id)
            except Exception:
                pass
        return live_chat_id

    def get_chat_messages(self, live_chat_id=None):
        """Fetch chat messages for a given live chat ID.

        If no ID is provided (e.g. during testing) return an empty list.
        """
        if live_chat_id is None:
            return []

        request = self.service.liveChat/messages().list(
            liveChatId=live_chat_id, part='snippet,authorDetails'
        )
        response = request.execute()
        return response.get('items', [])

    def close(self):
        # Placeholder for any cleanup if necessary
        pass