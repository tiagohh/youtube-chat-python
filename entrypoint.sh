#!/bin/bash
set -e

# Create output directories expected by the scraper
mkdir -p /app/Logs /app/firefox-profile

# ── 1. Virtual framebuffer (headless X display) ──────────────────────────────
Xvfb :99 -screen 0 1280x800x24 &
sleep 1

# ── 2. VNC server ─────────────────────────────────────────────────────────────
# Uses VNC_PASSWORD from .env if set; falls back to no-password mode.
if [ -n "$VNC_PASSWORD" ]; then
    x11vnc -display :99 -passwd "$VNC_PASSWORD" -forever -noxrecord \
           -noxfixes -noxdamage -quiet &
else
    x11vnc -display :99 -nopw -forever -noxrecord \
           -noxfixes -noxdamage -quiet &
fi
sleep 1

# ── 3. noVNC web proxy (port 6080) ────────────────────────────────────────────
websockify --web=/usr/share/novnc/ --wrap-mode=ignore 0.0.0.0:6080 localhost:5900 &
sleep 1

echo "============================================================"
echo "  Remote desktop → http://<your-server-ip>:6080/vnc.html"
if [ -n "$VNC_PASSWORD" ]; then
    echo "  VNC password : $VNC_PASSWORD"
fi
echo "  XLSX logs     → ./Logs/ on the host machine"
echo "============================================================"

# ── 4. YouTube live chat scraper ──────────────────────────────────────────────
exec python /app/src/docker_scraper.py
