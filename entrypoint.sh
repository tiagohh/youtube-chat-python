#!/bin/bash
set -e

# ── 1. Virtual framebuffer (headless X display) ─────────────────────────────
Xvfb :99 -screen 0 1280x800x24 &
sleep 1

# ── 2. VNC server that shares the Xvfb display ──────────────────────────────
# -nopw   : no VNC password (suitable for local/trusted network use)
# -forever: keep running after the first client disconnects
x11vnc -display :99 -nopw -listen localhost -xkb -forever -quiet &
sleep 1

# ── 3. noVNC web client on port 6080 ────────────────────────────────────────
# websockify bridges WebSocket (noVNC) ↔ plain TCP (x11vnc on 5900)
websockify --web=/usr/share/novnc/ --wrap-mode=ignore 0.0.0.0:6080 localhost:5900 &
sleep 1

echo "============================================================"
echo "  Remote desktop ready → http://<your-server-ip>:6080/vnc.html"
echo "  Navigate Firefox to your YouTube livestream to start logging."
echo "  CSV is saved to: ${CHAT_CSV_PATH}"
echo "============================================================"

# ── 4. Chat scraper (opens Firefox and monitors YouTube live chat) ───────────
exec python /app/src/docker_scraper.py
