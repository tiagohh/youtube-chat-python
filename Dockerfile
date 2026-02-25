FROM python:3.11-slim

# Install Firefox ESR, virtual display, VNC server, noVNC web client,
# geckodriver, and websockify (the WebSocket proxy for noVNC).
RUN apt-get update && apt-get install -y --no-install-recommends \
    firefox-esr \
    firefox-geckodriver \
    xvfb \
    x11vnc \
    novnc \
    websockify \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies (selenium only for the scraper)
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

COPY . .

RUN chmod +x /app/entrypoint.sh

# Virtual display that Firefox and noVNC will share
ENV DISPLAY=:99

# YouTube URL to open on startup. Leave blank to start on the YouTube
# homepage and navigate manually via noVNC.
ENV YOUTUBE_URL=https://www.youtube.com

# Path for the chat CSV inside the container (volume-mounted below)
ENV CHAT_CSV_PATH=/app/Logs/chat.csv

# Seconds between DOM polls
ENV POLL_INTERVAL=2

# noVNC web interface
EXPOSE 6080

ENTRYPOINT ["/app/entrypoint.sh"]
