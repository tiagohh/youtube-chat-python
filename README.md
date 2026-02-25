# YouTube Chat Python

This project is a Python application that connects to YouTube live chat and manages chat sessions amd saves in a csv file. It provides functionality to authenticate with the YouTube API, retrieve chat messages, and handle chat events.
WORK IN PROGRESS, LIKE IN PROGRESS, I don't know what I'm doing with my life

## Project Structure

```
youtube-chat-python
├── src
│   ├── youtube_chat.py          # Main script for managing YouTube chat
│   ├── client
│   │   ├── __init__.py          # Package initialization for client
│   │   └── youtube_client.py     # Handles YouTube API connection
│   ├── handlers
│   │   └── chat_handler.py       # Processes incoming chat messages
│   └── utils
│       └── auth.py               # Utility functions for authentication
├── tests
│   └── test_chat.py              # Unit tests for chat functionality
├── requirements.txt              # Project dependencies
├── .env.example                  # Example environment variables
├── .gitignore                    # Files to ignore by Git
└── README.md                     # Project documentation
```

## Download

A pre-built Windows executable is available on the [Releases page](https://github.com/tiagohh/youtube-chat-python/releases).
Download `YouTubeChatLogger.exe` from the latest release — no Python installation required.

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd youtube-chat-python
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up your environment variables:
   - Copy `.env.example` to `.env` and fill in your API keys and secrets.

## Usage

The project now includes a simple graphical interface and message logging.

### Credential prompt
If you don't want to hard‑code or export environment variables every time,
just run the script and a small dialog will ask for:

* **API key**
* **Video ID** (the ID of the YouTube video with live chat)

### Storage options

### Output folder structure

By default, all outputs are organized under a `Logs/` folder with subfolders for each type:

* `Logs/TXT/` — log files (e.g. `chat [YYYYMMDD_HHMMSS].log`)
* `Logs/Chat Principal CSV/` — CSV files (e.g. `chat [YYYYMMDD_HHMMSS].csv` or `chat.csv` for non-versioned runs)
* `Logs/ChatDatabase/` — SQLite database files (e.g. `chat [YYYYMMDD_HHMMSS].db`)

Each run creates a new, timestamped file for logs, CSV, and database by default. The CSV filename may be overridden with the `CHAT_CSV_FILE` environment variable.

You can disable the database or change its path by editing the `ChatHandler` instantiation in `src/youtube_chat.py`. The built-in helper used by the script already selects sensible default paths, so you normally don't need to change anything unless you want a different file location.

### Running
```
python src/youtube_chat.py
```

A window titled **YouTube Chat** will appear; enter or confirm credentials
when prompted and click **Connect**.  Messages will scroll in the window and
are available later in `chat.log` or the SQLite database.

You still may pre‑set the environment variables or use a `.env` file if you
prefer; the GUI will only prompt when values are missing.

> 💡 To bypass the GUI completely (e.g. for automated logging) simply
> instantiate `ChatHandler` without a `ui` object and call
> `chat.start_chat_session()` from your own script.
## Creating a Release

After merging changes into `main`, follow these steps to publish a new version with a Windows executable attached automatically:

1. **Tag the commit** with a version number (prefix `v` or `V`):
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **That's it.** Pushing the tag triggers the *Build Windows Executable* GitHub Actions workflow, which:
   - Builds `YouTubeChatLogger.exe` using PyInstaller on a Windows runner.
   - Creates a GitHub Release for the tag (if one doesn't exist yet) and attaches the `.exe` as a release asset.

3. **Check the result** on the [Releases page](https://github.com/tiagohh/youtube-chat-python/releases) — the new release should appear with `YouTubeChatLogger.exe` available for download within a few minutes.

> 💡 You can also go to **Actions → Build Windows Executable → Run workflow** to trigger a manual build at any time without pushing a tag (the exe will be saved as a workflow artifact instead of a release asset in that case).

## Contributing

Feel free to submit issues or pull requests for improvements or bug fixes.

## License

This project is licensed under the MIT License.

## Quota Usage Examples

### Example 1: 1-Hour Stream (Estimative)

If you stream for 1 hour with a polling interval of 18 seconds:

- **Seconds in 1 hour:** 3,600
- **Polling interval:** 18 seconds
- **Requests per hour:** 3,600 ÷ 18 = 200 requests
- **Quota units used:** 200 requests × 5 units = **1,000 units**

**Result:**  
A 1-hour stream at 18-second intervals will use about **1,000 units** of your daily 10,000-unit quota.

---

### Example 2: 10-Hour Stream (Estimative)

If you stream for 10 hours with a polling interval of 18 seconds:

- **Seconds in 10 hours:** 36,000
- **Polling interval:** 18 seconds
- **Requests per 10 hours:** 36,000 ÷ 18 = 2,000 requests
- **Quota units used:** 2,000 requests × 5 units = **10,000 units**

**Result:**  
A 10-hour stream at 18-second intervals will use your entire daily quota of **10,000 units**.

---

**Note:**  
Adjust the polling interval based on your planned streaming hours to avoid exceeding your daily quota. The quota resets every 24 hours. If your chat is very active, longer intervals may result in some messages not being captured.

---

## How to Change the Polling Interval (A Slightly Absurd Guide)

Adjusting the polling interval in your YouTube chat logger is a task best approached with a sense of curiosity and a mild disregard for the seriousness of software.

### Step 1: Find the Elusive Interval

Begin your quest by opening the mysterious file:
```
src/youtube_chat.py
```
This file is the nerve center of your chat-collecting operation, and somewhere within its digital depths lies the secret to your timing.

### Step 2: The Interval Revealed

Within the `YouTubeChat` class, inside the `start_chat_session` method, you’ll stumble upon a line that looks suspiciously like this:
```python
time.sleep(18)  # Polling interval
```
Or perhaps it’s another number, depending on the whims of your past self.

### Step 3: Change the Number, Change the World

Replace the number inside `time.sleep()` with your preferred interval in seconds. For example:
```python
time.sleep(10)  # Polling interval
```
Or, if you’re feeling particularly optimistic about your quota:
```python
time.sleep(30)  # Polling interval
```

### Step 4: Save and Restart

Save your changes. Then, as is the custom in the digital realm, restart your application so it can appreciate your newfound sense of timing.

### Step 5: The Unpredictable Nature of Chat

Remember:
- A smaller interval means you’ll catch more messages, but your quota will vanish faster than you can say “API limit exceeded.”
- A larger interval conserves quota, but in a lively chat, some messages may slip through the cracks, never to be seen again.

### In Summary

Edit the `time.sleep()` value, save, and restart your app. The universe may not notice, but your quota certainly will.

---

## TDC

YouTube livestream chat configuration can cause this issue. If the chat is set to "members only," "subscribers only," or is restricted by age, region, or moderation settings, the YouTube API may not return the live chat ID or messages, even if the stream is active. Also, if the stream is not truly live (e.g., it's a premiere or replay), the live chat may not be accessible via the API.

Check the following:

- The chat is public and not restricted to members/subscribers.
- The stream is currently live (not a replay or scheduled).
- There are no age or region restrictions.
- The API key has access to the required YouTube Data API scopes.


