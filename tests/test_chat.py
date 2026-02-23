import unittest
import os
import sqlite3
import csv
import subprocess
import sys
from src.client.youtube_client import YouTubeClient
from src.handlers.chat_handler import ChatHandler
from src.youtube_chat import YouTubeChat


class DummyUI:
    def __init__(self):
        self.messages = []

    def append_message(self, author, text):
        self.messages.append((author, text))


class TestYouTubeChat(unittest.TestCase):

    def setUp(self):
        self.client = YouTubeClient(api_key='test_api_key')
        self.ui = DummyUI()
        self.chat_handler = ChatHandler(self.client, ui=self.ui, log_file="test.log")

    def test_connection(self):
        self.assertTrue(self.client.connect())

    def test_retrieve_chat_messages(self):
        messages = self.client.get_chat_messages()
        self.assertIsInstance(messages, list)

    def test_process_chat_message(self):
        test_message = {'author': 'test_user', 'text': 'Hello, world!'}
        response = self.chat_handler.process_message(test_message)
        self.assertEqual(response, {"author": "test_user", "text": "Hello, world!"})
        # UI should have been updated
        self.assertIn(("test_user", "Hello, world!"), self.ui.messages)

    def test_structured_storage(self):
        # use a temporary sqlite database file
        db_file = "test_messages.db"
        if os.path.exists(db_file):
            # previous run may have left file open
            try:
                os.remove(db_file)
            except PermissionError:
                pass
        handler = ChatHandler(self.client, db_path=db_file)
        # also verify CSV output
        csv_file = "test_messages.csv"
        if os.path.exists(csv_file):
            os.remove(csv_file)
        handler_csv = ChatHandler(self.client, csv_path=csv_file)
        handler_csv.process_message({'author': 'carl', 'text': 'hola'})
        handler_csv.process_message({'author': 'dana', 'text': 'bye'})
        handler_csv.__del__()
        with open(csv_file, newline='', encoding='utf-8') as f:
            rows = list(csv.reader(f))
        # first row header (uppercase)
        self.assertEqual(rows[0], ["AUTHOR", "MESSAGE"])
        self.assertEqual(rows[1:], [["carl", "hola"], ["dana", "bye"]])
        os.remove(csv_file)
        handler.process_message({'author': 'alice', 'text': 'hi'})
        handler.process_message({'author': 'bob', 'text': 'bye'})
        # verify rows inserted
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        cur.execute("SELECT author,text FROM messages ORDER BY rowid")
        rows = cur.fetchall()
        conn.close()
        self.assertEqual(rows, [("alice", "hi"), ("bob", "bye")])
        handler._db_conn.close()
        os.remove(db_file)

    def test_project_handler_default_csv(self):
        # ensure the helper used by the main script assigns a default csv path
        from src.youtube_chat import create_handler
        import os
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        expected_csv = os.path.join(root, 'Logs', 'Chat Principal CSV', 'chat.csv')
        handler = create_handler(self.client, ui=self.ui)
        self.assertEqual(handler.csv_path, expected_csv)
        # override via environment variable
        os.environ["CHAT_CSV_FILE"] = "override.csv"
        handler2 = create_handler(self.client, ui=self.ui)
        self.assertEqual(handler2.csv_path, "override.csv")
        del os.environ["CHAT_CSV_FILE"]

    def test_video_id_lookup_and_cache(self):
        tmp = "tcache.tmp"
        if os.path.exists(tmp):
            os.remove(tmp)
        # patch YouTubeClient to simulate lookup and caching
        orig = YouTubeClient.get_live_chat_id
        def fake(self, vid, cache_file=None):
            if cache_file:
                with open(cache_file, 'w') as f:
                    f.write("ID123")
            return "ID123"
        YouTubeClient.get_live_chat_id = fake
        chat = YouTubeChat(api_key="k", video_id="vid", cache_file=tmp)
        self.assertEqual(chat.live_chat_id, "ID123")
        with open(tmp) as f:
            self.assertEqual(f.read(), "ID123")
        os.remove(tmp)
        # ensure normalization works with full URL
        tmp2 = "tcache2.tmp"
        YouTubeClient.get_live_chat_id = fake
        chat2 = YouTubeChat(api_key="k", video_id="https://www.youtube.com/watch?v=vid", cache_file=tmp2)
        self.assertEqual(chat2.live_chat_id, "ID123")
        with open(tmp2) as f:
            self.assertEqual(f.read(), "ID123")
        os.remove(tmp2)
        YouTubeClient.get_live_chat_id = orig


class TestYouTubeChatInvocation(unittest.TestCase):
    def test_invocation_as_script(self):
        """Test running youtube_chat.py as a script to catch token errors."""
        result = subprocess.run([
            sys.executable,
            os.path.join(os.path.dirname(__file__), '../src/youtube_chat.py')
        ], capture_output=True, text=True)
        # Check for known token error in output
        self.assertNotIn('Token', result.stderr)
        self.assertEqual(result.returncode, 0, msg=f"Script failed: {result.stderr}")


if __name__ == '__main__':
    unittest.main()
