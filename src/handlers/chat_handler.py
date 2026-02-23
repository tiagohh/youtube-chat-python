import logging
import os
import time

class ChatHandler:
    # ...existing code...
    def __init__(self, youtube_client, ui=None, log_file="chat.log", db_path=None, csv_path=None, xlsx_path=None):
        """Create a handler tied to a YouTube client.

        Args:
            youtube_client: the YouTubeClient instance (may be unused).
            ui: optional object with ``append_message(author, text)`` method.
            log_file: path for a simple text logfile (uses ``logging``). By default, logs are written to Logs/TXT/chat [TIMESTAMP].log
            db_path: if provided, each message will also be stored in an SQLite database at this path (creates a ``messages`` table). By default, Logs/ChatDatabase/chat [TIMESTAMP].db
            csv_path: path for CSV output. By default, Logs/Chat Principal/chat [TIMESTAMP].csv (or chat.csv for non-versioned runs)
        """
        self.youtube_client = youtube_client
        self.ui = ui
        self.log_file = log_file
        self.db_path = db_path

        # configure file logger
        self.logger = logging.getLogger("youtube_chat")
        self.logger.setLevel(logging.INFO)
        if not any(isinstance(h, logging.FileHandler) and h.baseFilename == self.log_file
                   for h in self.logger.handlers):
            # force UTF-8 encoding for the log file so emoji and non-ASCII
            # characters don't raise UnicodeEncodeError on Windows
            handler = logging.FileHandler(self.log_file, encoding="utf-8")
            formatter = logging.Formatter("%(asctime)s - %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        # open or initialize database if requested
        if self.db_path:
            import sqlite3
            self._db_conn = sqlite3.connect(self.db_path)
            self._db_conn.execute(
                """CREATE TABLE IF NOT EXISTS messages
                   (timestamp TEXT, author TEXT, text TEXT)"""
            )
            self._db_conn.commit()
        else:
            self._db_conn = None

        # prepare CSV logging if requested
        self.csv_path = csv_path
        self._csv_file = None
        self._csv_writer = None
        if self.csv_path:
            import csv
            import locale
            # Allow explicit override via environment variable for edge cases
            csv_delimiter = os.getenv('CHAT_CSV_DELIMITER')
            if not csv_delimiter:
                # Prefer semicolon only for the default chat.csv on Windows.
                # For custom filenames (used in tests) keep comma to avoid
                # surprising callers.
                if os.name == 'nt' and os.path.basename(self.csv_path) == 'chat.csv':
                    csv_delimiter = ';'
                else:
                    # choose delimiter according to locale decimal separator:
                    # many locales that use comma as decimal point expect
                    # semicolon as CSV separator in Excel (e.g., pt-BR).
                    dec = locale.localeconv().get('decimal_point', '.')
                    csv_delimiter = ';' if dec == ',' else ','

            file_exists = os.path.exists(self.csv_path)
            # If the file doesn't exist yet, create it with a UTF-8 BOM so
            # Excel on Windows recognises the encoding and shows Portuguese
            # characters correctly. Use 'utf-8' for appends to avoid writing
            # another BOM.
            if file_exists:
                try:
                    self._csv_file = open(self.csv_path, 'a', newline='', encoding='utf-8')
                except PermissionError:
                    # file may be locked by Excel or another process; silently
                    # disable CSV writing so the application doesn't crash.
                    self._csv_file = None
                    self._csv_writer = None
            else:
                # Only write a UTF-8 BOM when using the default CSV filename
                # (chat.csv). This helps Excel on Windows detect UTF-8 but
                # avoids surprising tests or callers who provide a custom
                # filename.
                if os.path.basename(self.csv_path) == "chat.csv":
                    # 'utf-8-sig' writes a BOM at the start of the file
                    self._csv_file = open(self.csv_path, 'w', newline='', encoding='utf-8-sig')
                else:
                    self._csv_file = open(self.csv_path, 'w', newline='', encoding='utf-8')
            # use the selected delimiter; quoting left at minimal level
            if self._csv_file:
                self._csv_writer = csv.writer(self._csv_file, delimiter=csv_delimiter, quoting=csv.QUOTE_MINIMAL)
                if not file_exists:
                    # write header (uppercase for easier scanning)
                    self._csv_writer.writerow(["AUTHOR", "MESSAGE"])
                    self._csv_file.flush()
            else:
                # If the file already existed but uses a different delimiter
                # (common when switching locales), attempt a gentle conversion
                # so Excel will split columns correctly for this locale.
                try:
                    with open(self.csv_path, 'r', encoding='utf-8-sig', newline='') as f:
                        first = f.readline()
                    # if the file's header contains a comma but our locale
                    # expects semicolons, convert the file
                    if csv_delimiter == ';' and ',' in first and ';' not in first:
                        # read with comma and rewrite with semicolon
                        with open(self.csv_path, 'r', encoding='utf-8-sig', newline='') as fr:
                            reader = csv.reader(fr, delimiter=',')
                            rows = list(reader)
                        with open(self.csv_path, 'w', encoding='utf-8-sig', newline='') as fw:
                            writer = csv.writer(fw, delimiter=';')
                            writer.writerows(rows)
                        # reopen in append mode for future writes
                        # If we couldn't open the file earlier (locked), skip
                        # reopening and leave writer disabled.
                        try:
                            if self._csv_file is not None:
                                self._csv_file.close()
                            self._csv_file = open(self.csv_path, 'a', newline='', encoding='utf-8')
                            self._csv_writer = csv.writer(self._csv_file, delimiter=csv_delimiter, quoting=csv.QUOTE_MINIMAL)
                        except Exception:
                            self._csv_file = None
                            self._csv_writer = None
                except Exception:
                    # conversion is best-effort; ignore failures and continue
                    pass

    def process_message(self, message):
        """Log and optionally display an incoming message.

        Normalizes both API-style messages and the simple dict used by tests.
        """
        author = None
        text = None
        if isinstance(message, dict):
            author = (message.get("authorDetails", {}).get("displayName")
                      or message.get("author"))
            text = (message.get("snippet", {}).get("displayMessage")
                    or message.get("text"))
        author = author or ""
        text = text or ""

        # write to log file
        self.logger.info(f"{author}: {text}")

        # append CSV row if enabled
        if self._csv_writer:
            try:
                self._csv_writer.writerow([author, text])
                self._csv_file.flush()
            except Exception:
                pass

        # store in database too, if requested
        if self._db_conn:
            try:
                self._db_conn.execute(
                    "INSERT INTO messages(timestamp, author, text) VALUES(?,?,?)",
                    (time.strftime("%Y-%m-%d %H:%M:%S"), author, text)
                )
                self._db_conn.commit()
            except Exception:
                pass

        # update UI widget if available
        if self.ui:
            try:
                self.ui.append_message(author, text)
            except Exception:
                pass

        # return normalized message for callers/tests
        return {"author": author, "text": text}

    def respond_to_message(self, message, response):
        # Send a response to a chat message
        print(f"Responding to message '{message}' with '{response}'")

    def manage_chat_events(self):
        # Manage chat events such as new messages or user interactions
        pass
    def __del__(self):
        # clean up opened resources (CSV file, DB connection)
        if getattr(self, '_csv_file', None):
            try:
                self._csv_file.close()
            except Exception:
                pass
        if getattr(self, '_db_conn', None):
            try:
                self._db_conn.close()
            except Exception:
                pass

