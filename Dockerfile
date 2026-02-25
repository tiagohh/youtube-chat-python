FROM python:3.11-slim

# Install Firefox ESR, virtual display, VNC server, noVNC web client,
# geckodriver, and websockify (the WebSocket-to-TCP proxy for noVNC).
RUN apt-get update && apt-get install -y --no-install-recommends \
    firefox-esr \
    firefox-geckodriver \
    xvfb \
    x11vnc \
    novnc \
    websockify \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

COPY . .

RUN chmod +x /app/entrypoint.sh

# ── Environment variables (override in .env or docker-compose.yml) ───────────

# Virtual display used by Xvfb, Firefox, and x11vnc
ENV DISPLAY=:99

# YouTube channel URL.  The scraper appends /live to find the current stream.
ENV YOUTUBE_CHANNEL_URL=https://www.youtube.com

# Directory inside the container where the XLSX file is written.
# This path is volume-mounted to ./Logs on the host.
ENV LOGS_DIR=/app/Logs

# Seconds between DOM polls (lower = more real-time, higher = less CPU)
ENV POLL_INTERVAL=2

# Seconds to wait before retrying when no livestream is found
ENV RETRY_INTERVAL=60

# VNC password for noVNC remote access (set a strong value in .env)
ENV VNC_PASSWORD=changeme

# noVNC web interface port
EXPOSE 6080

ENTRYPOINT ["/app/entrypoint.sh"]
