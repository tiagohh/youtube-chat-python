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

## Docker (remote Firefox + automatic chat logging)

Run Firefox inside a Docker container and control it from **any browser or
Android phone** via noVNC.  The chat scraper runs automatically as the
channel owner account — capturing all messages, mod actions, bans,
timeouts, and deleted messages — and writes everything to an **XLSX file**.

### XLSX output format

The file is saved to `./Logs/chat-YYYY-MM-DD_HH-MM-SS.xlsx` on your host
machine and contains **three sheets**:

| Sheet | Contents |
|---|---|
| `Chat` | Every message and moderation event |
| `VDS` | Banned users only (mirrored from Chat) |
| `Livestream URL` | The resolved stream URL captured at startup |

All sheets share **five columns** (light blue background, bold, uppercase headers):

| TIME | USER | MESSAGE | STATUS | MOD ACTION |
|---|---|---|---|---|
| 2026-02-25 10:30:01 | StreamFan99 | Hello everyone! | | |
| 2026-02-25 10:31:10 | BadActor | oops | `Deleted by user` | |
| 2026-02-25 10:32:00 | TrollUser | [offensive] | `Deleted by mod` | ModSarah |
| 2026-02-25 10:32:30 | SpamBot | Buy followers! | `Hidden` | |
| 2026-02-25 10:33:00 | TrollUser | again | `Timeout – 10 min` | ModJohn |
| 2026-02-25 10:34:00 | BannedUser | final message | `Banned` | ModSarah |

**STATUS values:** blank · `Deleted by user` · `Deleted by mod` · `Hidden` ·
`Timeout – X min` · `Banned`

Delayed mod actions (e.g. a message deleted 30 s after it was sent) update
the original row in-place so there is always one row per message.

### Services started by `docker compose up`

| Service | Purpose | Port |
|---|---|---|
| `youtube-chat` | Firefox + noVNC remote desktop + chat scraper | 6080 |
| `portainer` | Docker management UI (start/stop from Android) | 9443 |
| `cloudflared` | Secure tunnel — access both from outside your home | set in `.env` |

### Prerequisites

* [Docker](https://docs.docker.com/get-docker/) and
  [Docker Compose](https://docs.docker.com/compose/) installed on the
  machine that will run the containers (your home server or PC).
* A free [Cloudflare](https://dash.cloudflare.com) account for the tunnel
  (optional — remove the `cloudflared` service if you only need LAN access).

### First-time setup (do this once)

```bash
# 1. Clone the repository
git clone https://github.com/tiagohh/youtube-chat-python.git
cd youtube-chat-python

# 2. Create your .env file
cp .env.example .env
# Edit .env and fill in:
#   YOUTUBE_CHANNEL_URL  — your channel URL, e.g. https://www.youtube.com/@YourChannel
#   VNC_PASSWORD         — a strong password for the remote desktop
#   CLOUDFLARE_TUNNEL_TOKEN — from dash.cloudflare.com → Zero Trust → Tunnels

# 3. Start everything
docker compose up --build

# 4. Open the remote desktop in your browser
#    http://localhost:6080/vnc.html   (local)
#    https://your-tunnel.trycloudflare.com  (remote — see Cloudflare dashboard)

# 5. Log in to Google as the channel owner (only needed once)
#    Firefox saves the login to ./firefox-profile — it survives container restarts.
```

### Every time after that

```bash
docker compose up
```

Firefox opens already logged in, navigates to `YOUTUBE_CHANNEL_URL/live`,
and starts logging automatically.  The XLSX file appears in `./Logs/`.

### Remote management from Android

1. Open `https://localhost:9443` (or the Cloudflare tunnel URL) in your
   Android browser.
2. Log in to Portainer (set your admin password on first visit).
3. Tap **Start** on the `youtube-chat` container to begin a session.
4. Open the noVNC URL to watch Firefox in real time.

### Environment variables (`.env`)

| Variable | Default | Description |
|---|---|---|
| `YOUTUBE_CHANNEL_URL` | `https://www.youtube.com/@YourChannel` | Channel URL; the scraper appends `/live` to find the active stream |
| `VNC_PASSWORD` | `changeme` | Password for the noVNC remote desktop |
| `CLOUDFLARE_TUNNEL_TOKEN` | — | Tunnel token from Cloudflare dashboard |
| `POLL_INTERVAL` | `2` | Seconds between DOM reads |
| `RETRY_INTERVAL` | `60` | Seconds to wait before retrying if no stream is live |

### Security notes

* The VNC password is set in `.env` — use a strong, unique value.
* The Firefox profile (`./firefox-profile/`) contains your Google login
  cookies.  It is excluded from Git by `.gitignore` — never commit it.
* Portainer mounts the Docker socket (`/var/run/docker.sock`).  Keep
  Portainer behind the Cloudflare Tunnel (not directly exposed to the
  internet) and set a strong admin password.
* The Cloudflare Tunnel handles HTTPS encryption — no router ports need
  to be opened.

---

## Tampermonkey userscript (standalone, no Docker needed)

If you already have Firefox (or any Chromium-based browser) on your
device, you can install the userscript directly instead of using Docker.

1. Install [Tampermonkey](https://www.tampermonkey.net/) in your browser.
2. Open `tampermonkey/youtube_chat_logger.user.js` from this repository
   and click **Install** when Tampermonkey asks.
3. Navigate to any YouTube livestream — a **🔴 Chat Logger** panel appears
   in the bottom-right corner.
4. Click **⬇ Download XLSX** at any time to save the log.

The script captures the same five columns (`TIME`, `USER`, `MESSAGE`,
`STATUS`, `MOD ACTION`) across three sheets (`Chat`, `VDS`,
`Livestream URL`).  Delayed mod actions update the original row in-place,
so there is always one row per message regardless of when the action occurs.

> **Note:** The XLSX generated by the browser script does not have the
> light-blue styled headers (browser XLSX libraries do not easily support
> cell styling).  The Docker/Python version produces fully styled output.

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


