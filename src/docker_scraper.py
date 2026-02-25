"""docker_scraper.py – Selenium-based YouTube live chat logger.

Opens a **visible** Firefox window (shown via Xvfb/noVNC so you can watch
and control it remotely) and monitors YouTube live chat using a JavaScript
MutationObserver injected into the page.

Chat messages are written to a CSV file with four columns:
    time      – ISO-8601 timestamp when the message was captured
    name      – display name of the author
    message   – message text
    delete?   – "yes" if the message was removed (deleted by moderator/author)

Environment variables
---------------------
YOUTUBE_URL     URL to open on start (default: https://www.youtube.com).
                Set to a livestream URL to skip manual navigation.
CHAT_CSV_PATH   Output CSV path (default: /app/Logs/chat.csv).
POLL_INTERVAL   Seconds between DOM reads (default: 2).
"""

import csv
import logging
import os
import time
from datetime import datetime, timezone

from selenium import webdriver
from selenium.common.exceptions import JavascriptException, WebDriverException
from selenium.webdriver.firefox.options import Options

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("docker_scraper")

YOUTUBE_URL = os.getenv("YOUTUBE_URL", "https://www.youtube.com")
CSV_PATH = os.getenv("CHAT_CSV_PATH", "/app/Logs/chat.csv")
POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "2"))

# ---------------------------------------------------------------------------
# JavaScript injected into the YouTube live-chat iframe.
# Installs a MutationObserver that pushes every new/removed message into
# window._ytChatLog so Python can read it with a simple execute_script call.
# ---------------------------------------------------------------------------
_JS_SETUP = """
if (!window._ytChatMonitorInstalled) {
    window._ytChatLog = [];
    window._ytChatMonitorInstalled = false;

    function _captureMsg(el, isDeleted) {
        try {
            var id   = el.getAttribute('id') || el.getAttribute('data-id') || '';
            var nameEl = el.querySelector('#author-name, .yt-live-chat-author-chip #author-name');
            var msgEl  = el.querySelector('#message');
            var name = nameEl ? nameEl.textContent.trim() : '';
            var msg  = msgEl  ? msgEl.textContent.trim()  : '';
            if (!name && !msg) return;
            window._ytChatLog.push({
                id:      id,
                name:    name,
                message: msg,
                time:    new Date().toISOString(),
                deleted: isDeleted ? 'yes' : ''
            });
        } catch(e) {}
    }

    var container = document.querySelector(
        '#items.yt-live-chat-item-list-renderer, ' +
        'yt-live-chat-item-list-renderer #items'
    );
    if (container) {
        // capture already-visible messages
        container.querySelectorAll(
            'yt-live-chat-text-message-renderer,' +
            'yt-live-chat-paid-message-renderer'
        ).forEach(function(el) { _captureMsg(el, false); });

        var obs = new MutationObserver(function(muts) {
            muts.forEach(function(m) {
                m.addedNodes.forEach(function(n) {
                    if (n.nodeType === 1) _captureMsg(n, false);
                });
                m.removedNodes.forEach(function(n) {
                    if (n.nodeType === 1 &&
                            n.tagName && n.tagName.toLowerCase().indexOf('yt-live-chat') === 0) {
                        _captureMsg(n, true);
                    }
                });
            });
        });
        obs.observe(container, {childList: true});
        window._ytChatMonitorInstalled = true;
    }
}
return window._ytChatMonitorInstalled;
"""

_JS_READ = """
var log = window._ytChatLog || [];
window._ytChatLog = [];
return log;
"""

_JS_IS_ALIVE = """
return !!(window._ytChatMonitorInstalled);
"""


def _ensure_logs_dir(path: str) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)


def _open_csv(path: str):
    _ensure_logs_dir(path)
    file_exists = os.path.exists(path)
    # utf-8-sig writes a BOM so Excel opens the file correctly
    f = open(path, "a", newline="", encoding="utf-8-sig")
    writer = csv.writer(f)
    if not file_exists:
        writer.writerow(["time", "name", "message", "delete?"])
        f.flush()
    return f, writer


def _switch_to_chat_frame(driver) -> bool:
    """Switch into the live-chat iframe when present; stays at root otherwise."""
    driver.switch_to.default_content()
    try:
        frames = driver.find_elements("css selector", "iframe#chatframe")
        if frames:
            driver.switch_to.frame(frames[0])
            return True
    except Exception:
        pass
    return False


def _iso_to_local(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main() -> None:
    log.info("Starting Firefox…")
    options = Options()
    # Do NOT use headless mode – the window must be visible via noVNC
    driver = webdriver.Firefox(options=options)
    driver.maximize_window()

    log.info("Opening %s", YOUTUBE_URL)
    driver.get(YOUTUBE_URL)

    csv_file, writer = _open_csv(CSV_PATH)
    log.info("CSV → %s", CSV_PATH)

    seen_ids: set = set()
    monitor_installed = False

    log.info(
        "Waiting for a YouTube livestream… "
        "Navigate to a live video in Firefox (via noVNC) to start logging."
    )

    while True:
        try:
            _switch_to_chat_frame(driver)

            # Try to (re-)install the observer if not yet active
            if not monitor_installed:
                try:
                    monitor_installed = bool(driver.execute_script(_JS_SETUP))
                except JavascriptException:
                    pass

            # Read messages accumulated by the observer
            if monitor_installed:
                try:
                    events = driver.execute_script(_JS_READ) or []
                except JavascriptException:
                    events = []
                    monitor_installed = False

                for ev in events:
                    eid = ev.get("id", "")
                    name = ev.get("name", "")
                    message = ev.get("message", "")
                    deleted = ev.get("deleted", "")
                    ts = _iso_to_local(ev.get("time", ""))

                    if deleted == "yes":
                        # Log a deletion event (message removed by moderator/author)
                        writer.writerow([ts, name, message or "[deleted]", "yes"])
                        csv_file.flush()
                        log.info("[DELETED] %s: %s", name, message)
                        seen_ids.discard(eid)
                    elif eid not in seen_ids:
                        seen_ids.add(eid)
                        writer.writerow([ts, name, message, ""])
                        csv_file.flush()
                        log.info("%s: %s", name, message)

                # Check if the observer is still alive (page navigation resets it)
                try:
                    if not bool(driver.execute_script(_JS_IS_ALIVE)):
                        monitor_installed = False
                except Exception:
                    monitor_installed = False

        except WebDriverException as exc:
            log.warning("WebDriver error (browser navigating?): %s", exc)
            monitor_installed = False
            time.sleep(3)
        except Exception as exc:
            log.error("Unexpected error: %s", exc)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
