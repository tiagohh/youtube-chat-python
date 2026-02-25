from googleapiclient.discovery import build
import os
import time
import googleapiclient.errors

# helper to construct a ChatHandler with sane defaults.  moved here so
# tests can import it and so that the main script uses the same logic.
#
# `csv_path` defaults to the value of the CHAT_CSV_FILE environment
# variable or `chat.csv` when unset.
def create_handler(youtube_client, ui=None, log_file="chat.log",
                   db_path="chat.db", csv_path=None, versioned=False):
    from src.handlers.chat_handler import ChatHandler
    # Environment variable takes precedence
    env_csv = os.getenv("CHAT_CSV_FILE")
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Logs')
    txt_dir = os.path.join(logs_dir, 'TXT')
    db_dir = os.path.join(logs_dir, 'ChatDatabase')
    csv_dir = os.path.join(logs_dir, 'Chat Principal CSV')
    xlsx_dir = os.path.join(logs_dir, 'Chat principal com emotes')
    os.makedirs(xlsx_dir, exist_ok=True)

    xlsx_path = os.path.join(xlsx_dir, f"chat [{timestamp}].xlsx")
    os.makedirs(txt_dir, exist_ok=True)
    os.makedirs(db_dir, exist_ok=True)
    os.makedirs(csv_dir, exist_ok=True)

    if log_file is None or log_file == "chat.log":
        log_file = os.path.join(txt_dir, f"chat [{timestamp}].log")
    if db_path is None or db_path == "chat.db":
        db_path = os.path.join(db_dir, f"chat [{timestamp}].db")
    if csv_path is None:
        if env_csv:
            csv_path = env_csv
        else:
            if versioned:
                csv_path = os.path.join(csv_dir, f"chat [{timestamp}].csv")
            else:
                csv_path = os.path.join(csv_dir, "chat.csv")

    print(
        f"\nFiles will be saved to:\n"
        f"  Log : {log_file}\n"
        f"  CSV : {csv_path}\n"
        f"  DB  : {db_path}\n"
        f"  XLSX: {xlsx_path}\n"
    )

    prev = os.environ.get('CHAT_CSV_DELIMITER')
    try:
        if versioned and os.name == 'nt' and prev is None:
            os.environ['CHAT_CSV_DELIMITER'] = ';'
        return ChatHandler(youtube_client, ui=ui,
                           log_file=log_file,
                           db_path=db_path,
                           csv_path=csv_path,
                           xlsx_path=xlsx_path)
    finally:
        if prev is None and 'CHAT_CSV_DELIMITER' in os.environ:
            del os.environ['CHAT_CSV_DELIMITER']
        elif prev is not None:
            os.environ['CHAT_CSV_DELIMITER'] = prev


class YouTubeChat:
    def __init__(self, api_key, live_chat_id=None, video_id=None, cache_file=None, handler=None):
        """Manage a chat session.

        Either `live_chat_id` or `video_id` must be provided.  If a video
        ID is given the live chat ID is looked up and optionally cached to
        `cache_file`.
        """
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
        self.handler = handler
        if live_chat_id:
            self.live_chat_id = live_chat_id
        elif video_id:
            from src.client.youtube_client import YouTubeClient
            client = YouTubeClient(api_key)
            self.live_chat_id = client.get_live_chat_id(video_id, cache_file=cache_file)
        else:
            raise ValueError("either live_chat_id or video_id must be provided")

    def get_live_chat_messages(self):
        # note: use the correct service name `liveChatMessages`
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                response = self.youtube.liveChatMessages().list(
                    liveChatId=self.live_chat_id,
                    part='snippet,authorDetails'
                ).execute()
                # print(f"[DEBUG] liveChatMessages API response (attempt {attempt+1}):", response)
                return response.get('items', [])
            except Exception as exc:
                print(f"[EXCEPTION] Exception in get_live_chat_messages (attempt {attempt+1}): {exc}")
                import traceback
                traceback.print_exc()
                if attempt == max_retries:
                    raise
                else:
                    import time
                    time.sleep(2)  # Wait 2 seconds before retrying

    def start_chat_session(self):
        """Poll the YouTube API forever, forwarding each message to the handler."""
        print("Starting YouTube chat session...")  # User-facing info, keep this
        while True:
            try:
                messages = self.get_live_chat_messages()
                for message in messages:
                    if self.handler:
                        self.handler.process_message(message)
                    else:
                        # fallback if no handler was supplied
                        author = message.get('authorDetails', {}).get('displayName')
                        text = message.get('snippet', {}).get('displayMessage')
                        print(f"{author}: {text}")
                time.sleep(18)  # Polling interval
            except Exception as exc:
                print(f"[EXCEPTION] Exception in start_chat_session polling loop: {exc}")
                import traceback
                traceback.print_exc()
                raise


if __name__ == "__main__":
    # make sure workspace root is on the import path so `src` is a package
    import sys
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if root not in sys.path:
        sys.path.insert(0, root)

    # Obtain credentials from environment or prompt the user.
    API_KEY = os.getenv('YOUTUBE_API_KEY')
    LIVE_CHAT_ID = os.getenv('YOUTUBE_LIVE_CHAT_ID')
    VIDEO_ID = os.getenv('YOUTUBE_VIDEO_ID')
    CACHE_FILE = os.getenv('CHAT_ID_CACHE_FILE', "chat_id.cache")

    # print(f"[DEBUG] Initial API_KEY: {API_KEY}")
    # print(f"[DEBUG] Initial LIVE_CHAT_ID: {LIVE_CHAT_ID}")
    # print(f"[DEBUG] Initial VIDEO_ID: {VIDEO_ID}")
    # print(f"[DEBUG] CACHE_FILE: {CACHE_FILE}")

    # helper that strips a full youtube link down to the raw ID
    import re
    def normalize_video_id(val):
        if not val:
            return val
        # common patterns: v=ID, youtu.be/ID
        m = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", val)
        if m:
            return m.group(1)
        return val

    # start UI for optional prompting and display
    try:
        from src.ui.chat_ui import ChatUI
        ui = ChatUI()
    except Exception:
        ui = None

    if not API_KEY or (not LIVE_CHAT_ID and not VIDEO_ID):
        if ui is None:
            # tkinter not available and no credentials; exit gracefully
            print("No credentials provided and no UI available.")
            sys.exit(0)
        api, vid = ui.prompt_credentials()
        API_KEY = API_KEY or api
        VIDEO_ID = VIDEO_ID or vid
        # print(f"[DEBUG] User provided API_KEY: {API_KEY}")
        # print(f"[DEBUG] User provided VIDEO_ID: {VIDEO_ID}")

    # normalize video input (may be full URL)
    VIDEO_ID = normalize_video_id(VIDEO_ID)
    # print(f"[DEBUG] Normalized VIDEO_ID: {VIDEO_ID}")

    if not API_KEY or (not LIVE_CHAT_ID and not VIDEO_ID):
        error_msg = "API key and either Live Chat ID (via env) or Video ID must be provided."
        print(error_msg)
        try:
            from tkinter import messagebox
            messagebox.showerror("API Key Error", error_msg)
        except Exception:
            pass
        try:
            ui.root.destroy()
        except Exception:
            pass
    else:
        try:
            from src.client.youtube_client import YouTubeClient
            from src.handlers.chat_handler import ChatHandler


            yt_client = YouTubeClient(API_KEY)
            # print(f"[DEBUG] Creating YouTubeChat with API_KEY: {API_KEY}, LIVE_CHAT_ID: {LIVE_CHAT_ID}, VIDEO_ID: {VIDEO_ID}, CACHE_FILE: {CACHE_FILE}")
            # create a new, timestamped CSV for this run so logs are versioned
            handler = create_handler(yt_client, ui=ui, versioned=True)
            chat = YouTubeChat(
                API_KEY,
                live_chat_id=LIVE_CHAT_ID,
                video_id=VIDEO_ID,
                cache_file=CACHE_FILE,
                handler=handler,
            )
            # print(f"[DEBUG] YouTubeChat created. live_chat_id: {getattr(chat, 'live_chat_id', None)}")

            import threading
            def run_poll():
                try:
                    chat.start_chat_session()
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    def show_error():
                        try:
                            from tkinter import messagebox
                            messagebox.showerror("Runtime error", str(e))
                        except Exception:
                            pass
                        try:
                            ui.root.destroy()
                        except Exception:
                            pass
                    try:
                        ui.root.after(0, show_error)
                    except Exception:
                        pass
            poll_thread = threading.Thread(target=run_poll, daemon=True)
            poll_thread.start()

            ui.start()
        except Exception as exc:
            print("Failed to start chat:", exc)
            try:
                from tkinter import messagebox
                messagebox.showerror("Startup error", str(exc))
            except Exception:
                pass
