FROM python:3.11-slim

# Install Firefox ESR, Xvfb, tkinter, and display utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    firefox-esr \
    xvfb \
    x11-utils \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV DISPLAY=:99

ENTRYPOINT ["/entrypoint.sh"]
