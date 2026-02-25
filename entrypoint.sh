#!/bin/bash
set -e

# Start the virtual framebuffer display
Xvfb :99 -screen 0 1280x720x24 &

# Give Xvfb a moment to initialise
sleep 1

# Start Firefox in the background
firefox &

# Run the YouTube chat logger
exec python src/youtube_chat.py
