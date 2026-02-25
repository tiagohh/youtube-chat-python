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
        """Return the live chat ID for a video. Caching is disabled."""
        try:
            request = self.service.videos().list(part='liveStreamingDetails', id=video_id)
            response = request.execute()
            # Store the API response in a file for debugging
            import json
            with open("youtube_api_response.json", "w", encoding="utf-8") as f:
                json.dump(response, f, ensure_ascii=False, indent=2)
            # print("[DEBUG] YouTube API response for liveStreamingDetails written to youtube_api_response.json")
            items = response.get('items', [])
            if not items:
                print(f"[ERROR] No video found with ID '{video_id}'. Please check the video ID and try again.")
                raise ValueError(f"No video found with ID '{video_id}'. Please check the video ID and try again.")
            live_details = items[0].get('liveStreamingDetails', {})
            # print("[DEBUG] liveStreamingDetails:", live_details)
            live_chat_id = live_details.get('activeLiveChatId')
            if not live_chat_id:
                # Provide a clear error if the video is not live or chat is unavailable
                if 'actualStartTime' not in live_details:
                    print("[ERROR] This video is not currently live. Please select a live stream.")
                    raise ValueError("This video is not currently live. Please select a live stream.")
                else:
                    print("[ERROR] Live chat is not available for this video. It may be disabled or ended.")
                    raise ValueError("Live chat is not available for this video. It may be disabled or ended.")
            return live_chat_id
        except Exception as exc:
            print(f"[EXCEPTION] Exception in get_live_chat_id: {exc}")
            import traceback
            traceback.print_exc()
            raise

    def get_chat_messages(self, live_chat_id=None):
        """Fetch chat messages for a given live chat ID.

        If no ID is provided (e.g. during testing) return an empty list.
        """
        if live_chat_id is None:
            return []

        request = self.service.liveChatMessages().list(
            liveChatId=live_chat_id, part='snippet,authorDetails'
        )
        response = request.execute()
        return response.get('items', [])

    def close(self):
        # Placeholder for any cleanup if necessary
        pass