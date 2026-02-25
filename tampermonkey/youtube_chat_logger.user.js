// ==UserScript==
// @name         YouTube Live Chat Logger
// @namespace    https://github.com/tiagohh/youtube-chat-python
// @version      2.0
// @description  Logs YouTube live chat messages (with mod actions, bans, timeouts) and downloads the log as an XLSX file with three sheets: Chat, VDS (bans), Livestream URL.
// @author       tiagohh
// @match        *://www.youtube.com/*
// @require      https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js
// @grant        GM_addStyle
// @run-at       document-idle
// ==/UserScript==

(function () {
    'use strict';

    // ── Storage ───────────────────────────────────────────────────────────────
    // Each entry: { id, time, name, message, status, modAction }
    const log     = [];
    const byId    = {};   // id → index in log[] for in-place updates

    // ── Helpers ───────────────────────────────────────────────────────────────

    function nowStr() {
        const d   = new Date();
        const pad = n => String(n).padStart(2, '0');
        return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ` +
               `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
    }

    /** Try to parse a moderation system message into { name, status }. */
    function parseSystemMsg(el) {
        const textEl = el.querySelector('#text, yt-formatted-string#text, .message');
        const text   = textEl ? textEl.textContent.trim() : el.textContent.trim();
        if (!text) return null;

        // Timeout: "Username was timed out for X minutes"
        const tmo = text.match(/^(.+?)\s+was timed out for\s+(\d+)\s*(\w+)/i);
        if (tmo) return { name: tmo[1].trim(),
                          status: `Timeout \u2013 ${tmo[2]} ${tmo[3]}` };

        // Ban: "Username has been removed" / "Username was banned"
        const ban = text.match(/^(.+?)\s+(has been removed|was banned)/i);
        if (ban) return { name: ban[1].trim(), status: 'Banned' };

        return null;
    }

    // ── Capture functions ─────────────────────────────────────────────────────

    function captureNew(el) {
        const tag = el.tagName?.toLowerCase() ?? '';

        // System messages (timeouts / bans)
        if (tag === 'yt-live-chat-system-message-renderer') {
            const parsed = parseSystemMsg(el);
            if (!parsed) return;
            const entry = { id: '', time: nowStr(), name: parsed.name,
                            message: '', status: parsed.status, modAction: '' };
            log.push(entry);
            if (parsed.status === 'Banned') updateCounter();
            else updateCounter();
            return;
        }

        // Regular / Super Chat messages
        if (tag !== 'yt-live-chat-text-message-renderer' &&
            tag !== 'yt-live-chat-paid-message-renderer') return;

        const id      = el.id || el.getAttribute('data-id') || '';
        const nameEl  = el.querySelector('#author-name');
        const msgEl   = el.querySelector('#message');
        const name    = nameEl ? nameEl.textContent.trim() : '';
        const message = msgEl  ? msgEl.textContent.trim()  : '';
        if (!name && !message) return;
        if (id && id in byId) return;  // already captured

        const entry = { id, time: nowStr(), name, message, status: '', modAction: '' };
        const idx   = log.length;
        log.push(entry);
        if (id) byId[id] = idx;
        updateCounter();
    }

    function captureRemoved(el) {
        const tag = el.tagName?.toLowerCase() ?? '';
        if (tag !== 'yt-live-chat-text-message-renderer' &&
            tag !== 'yt-live-chat-paid-message-renderer') return;

        const id      = el.id || el.getAttribute('data-id') || '';
        const nameEl  = el.querySelector('#author-name');
        const msgEl   = el.querySelector('#message');
        const name    = nameEl ? nameEl.textContent.trim() : '';
        const message = msgEl  ? msgEl.textContent.trim()  : '';

        if (id && id in byId) {
            // Update the original entry in-place (delayed mod action)
            log[byId[id]].status = 'Deleted by mod';
        } else {
            const entry = { id, time: nowStr(), name, message,
                            status: 'Deleted by mod', modAction: '' };
            const idx   = log.length;
            log.push(entry);
            if (id) byId[id] = idx;
        }
        updateCounter();
    }

    // ── MutationObserver ──────────────────────────────────────────────────────

    let observer = null;

    function installObserver() {
        if (observer) { observer.disconnect(); observer = null; }

        const chatFrame = document.querySelector('iframe#chatframe');
        const doc       = chatFrame ? chatFrame.contentDocument : document;
        if (!doc) return false;

        const container = doc.querySelector(
            '#items.yt-live-chat-item-list-renderer, ' +
            'yt-live-chat-item-list-renderer #items'
        );
        if (!container) return false;

        // Capture already-visible messages
        container.querySelectorAll(
            'yt-live-chat-text-message-renderer, ' +
            'yt-live-chat-paid-message-renderer, ' +
            'yt-live-chat-system-message-renderer'
        ).forEach(el => captureNew(el));

        observer = new MutationObserver(muts => {
            for (const m of muts) {
                for (const n of m.addedNodes)
                    if (n.nodeType === 1) captureNew(n);
                for (const n of m.removedNodes)
                    if (n.nodeType === 1) captureRemoved(n);
            }
        });
        observer.observe(container, { childList: true });
        return true;
    }

    // ── XLSX export (3 sheets) ────────────────────────────────────────────────

    const HEADERS = ['TIME', 'USER', 'MESSAGE', 'STATUS', 'MOD ACTION'];

    function makeSheet(rows) {
        const ws    = XLSX.utils.aoa_to_sheet(rows);
        ws['!cols'] = [{ wch: 22 }, { wch: 22 }, { wch: 55 }, { wch: 20 }, { wch: 20 }];
        return ws;
    }

    function downloadXLSX() {
        const wb = XLSX.utils.book_new();

        // Sheet 1 – Chat (all messages)
        const chatRows = [HEADERS, ...log.map(e =>
            [e.time, e.name, e.message, e.status, e.modAction])];
        XLSX.utils.book_append_sheet(wb, makeSheet(chatRows), 'Chat');

        // Sheet 2 – VDS (banned users only)
        const vdsRows = [HEADERS, ...log
            .filter(e => e.status === 'Banned')
            .map(e => [e.time, e.name, e.message, e.status, e.modAction])];
        XLSX.utils.book_append_sheet(wb, makeSheet(vdsRows), 'VDS');

        // Sheet 3 – Livestream URL
        const urlRows = [['LIVESTREAM URL'], [window.location.href]];
        XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(urlRows), 'Livestream URL');

        XLSX.writeFile(wb, `youtube-chat-${Date.now()}.xlsx`);
    }

    // ── Floating UI panel ─────────────────────────────────────────────────────

    GM_addStyle(`
        #ytcl-panel {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 999999;
            background: rgba(15,15,15,0.92);
            color: #fff;
            border-radius: 10px;
            padding: 12px 16px;
            font: 13px/1.5 'Roboto', sans-serif;
            min-width: 180px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.6);
            user-select: none;
        }
        #ytcl-panel .ytcl-title  { font-weight:bold; font-size:14px; margin-bottom:4px; }
        #ytcl-panel .ytcl-count  { font-size:20px; font-weight:bold; color:#ff4444; }
        #ytcl-panel button {
            display:block; width:100%; margin-top:8px; padding:6px 10px;
            border:none; border-radius:6px; cursor:pointer;
            font-size:13px; font-weight:bold; transition:background 0.15s;
        }
        #ytcl-btn-download { background:#cc0000; color:#fff; }
        #ytcl-btn-download:hover { background:#990000; }
        #ytcl-btn-clear    { background:#444; color:#ccc; }
        #ytcl-btn-clear:hover { background:#666; }
        #ytcl-status { font-size:11px; color:#aaa; margin-top:6px; }
    `);

    const panel = document.createElement('div');
    panel.id = 'ytcl-panel';
    panel.innerHTML = `
        <div class="ytcl-title">🔴 Chat Logger</div>
        <div>Messages: <span class="ytcl-count" id="ytcl-count">0</span></div>
        <button id="ytcl-btn-download">⬇ Download XLSX</button>
        <button id="ytcl-btn-clear">🗑 Clear log</button>
        <div class="ytcl-status" id="ytcl-status">Waiting for livestream…</div>
    `;
    document.body.appendChild(panel);

    document.getElementById('ytcl-btn-download').addEventListener('click', downloadXLSX);
    document.getElementById('ytcl-btn-clear').addEventListener('click', () => {
        log.length = 0;
        Object.keys(byId).forEach(k => delete byId[k]);
        updateCounter();
    });

    function updateCounter() {
        const el = document.getElementById('ytcl-count');
        if (el) el.textContent = log.length;
    }

    function setStatus(msg) {
        const el = document.getElementById('ytcl-status');
        if (el) el.textContent = msg;
    }

    // ── Auto-attach polling ───────────────────────────────────────────────────
    // The live-chat iframe loads after the main page — poll until it appears.

    let installed = false;
    let retries   = 0;

    const attachInterval = setInterval(() => {
        if (installObserver()) {
            installed = true;
            setStatus('✅ Logging chat…');
            clearInterval(attachInterval);
        } else if (++retries > 60) {
            setStatus('No live chat found.');
            clearInterval(attachInterval);
        }
    }, 1000);

    // Re-attach after YouTube SPA navigation
    new MutationObserver(() => {
        if (!installed || observer) return;
        installed = false;
        retries   = 0;
        setStatus('Reattaching…');
        const ri = setInterval(() => {
            if (installObserver()) {
                installed = true;
                setStatus('✅ Logging chat…');
                clearInterval(ri);
            } else if (++retries > 30) {
                setStatus('No live chat found.');
                clearInterval(ri);
            }
        }, 1000);
    }).observe(document.body, { childList: true, subtree: false });

})();


(function () {
    'use strict';

    // ── Storage ──────────────────────────────────────────────────────────────
    const log     = [];       // array of { id, time, name, message, deleted }
    const seenIds = new Set();
    let   observer = null;

    // ── Helpers ───────────────────────────────────────────────────────────────

    /** Return "YYYY-MM-DD HH:MM:SS" in the local timezone. */
    function nowStr() {
        const d  = new Date();
        const pad = n => String(n).padStart(2, '0');
        return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ` +
               `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
    }

    /** Capture one chat renderer element into the log. */
    function capture(el, isDeleted) {
        const id      = el.getAttribute('id') || el.getAttribute('data-id') || '';
        const nameEl  = el.querySelector('#author-name, .yt-live-chat-author-chip #author-name');
        const msgEl   = el.querySelector('#message');
        const name    = nameEl ? nameEl.textContent.trim() : '';
        const message = msgEl  ? msgEl.textContent.trim()  : '';

        if (!name && !message) return;

        const entry = { id, time: nowStr(), name, message, deleted: isDeleted ? 'yes' : '' };

        if (isDeleted) {
            // Mark a previously-seen message as deleted
            log.push(entry);
            updateCounter();
        } else if (!seenIds.has(id)) {
            seenIds.add(id);
            log.push(entry);
            updateCounter();
        }
    }

    // ── MutationObserver ──────────────────────────────────────────────────────

    function installObserver() {
        if (observer) { observer.disconnect(); observer = null; }

        // YouTube live chat lives inside an <iframe id="chatframe">
        const chatFrame = document.querySelector('iframe#chatframe');
        const doc       = chatFrame ? chatFrame.contentDocument : document;
        if (!doc) return false;

        const container = doc.querySelector(
            '#items.yt-live-chat-item-list-renderer, ' +
            'yt-live-chat-item-list-renderer #items'
        );
        if (!container) return false;

        // Capture messages already visible in the chat
        container.querySelectorAll(
            'yt-live-chat-text-message-renderer, yt-live-chat-paid-message-renderer'
        ).forEach(el => capture(el, false));

        observer = new MutationObserver(muts => {
            for (const m of muts) {
                for (const n of m.addedNodes)
                    if (n.nodeType === 1) capture(n, false);
                for (const n of m.removedNodes)
                    if (n.nodeType === 1 && n.tagName?.toLowerCase().startsWith('yt-live-chat'))
                        capture(n, true);
            }
        });
        observer.observe(container, { childList: true });
        return true;
    }

    // ── CSV export ────────────────────────────────────────────────────────────

    function escapeCSV(val) {
        return '"' + String(val ?? '').replace(/"/g, '""') + '"';
    }

    function buildCSV() {
        const header = ['time', 'name', 'message', 'delete?'].map(escapeCSV).join(',');
        const rows   = log.map(e =>
            [e.time, e.name, e.message, e.deleted].map(escapeCSV).join(',')
        );
        return [header, ...rows].join('\r\n');
    }

    function downloadCSV() {
        const blob = new Blob([buildCSV()], { type: 'text/csv;charset=utf-8;' });
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href     = url;
        a.download = `youtube-chat-${Date.now()}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // ── Floating UI panel ─────────────────────────────────────────────────────

    GM_addStyle(`
        #ytcl-panel {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 999999;
            background: rgba(15, 15, 15, 0.92);
            color: #fff;
            border-radius: 10px;
            padding: 12px 16px;
            font: 13px/1.5 'Roboto', sans-serif;
            min-width: 170px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.6);
            user-select: none;
        }
        #ytcl-panel .ytcl-title {
            font-weight: bold;
            font-size: 14px;
            margin-bottom: 4px;
        }
        #ytcl-panel .ytcl-count {
            font-size: 20px;
            font-weight: bold;
            color: #ff4444;
        }
        #ytcl-panel button {
            display: block;
            width: 100%;
            margin-top: 8px;
            padding: 6px 10px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: bold;
            transition: background 0.15s;
        }
        #ytcl-btn-download { background: #cc0000; color: #fff; }
        #ytcl-btn-download:hover { background: #990000; }
        #ytcl-btn-clear    { background: #444; color: #ccc; }
        #ytcl-btn-clear:hover { background: #666; }
        #ytcl-status {
            font-size: 11px;
            color: #aaa;
            margin-top: 6px;
        }
    `);

    const panel = document.createElement('div');
    panel.id = 'ytcl-panel';
    panel.innerHTML = `
        <div class="ytcl-title">🔴 Chat Logger</div>
        <div>Messages: <span class="ytcl-count" id="ytcl-count">0</span></div>
        <button id="ytcl-btn-download">⬇ Download CSV</button>
        <button id="ytcl-btn-clear">🗑 Clear log</button>
        <div class="ytcl-status" id="ytcl-status">Waiting for livestream…</div>
    `;
    document.body.appendChild(panel);

    document.getElementById('ytcl-btn-download').addEventListener('click', downloadCSV);
    document.getElementById('ytcl-btn-clear').addEventListener('click', () => {
        log.length = 0;
        seenIds.clear();
        updateCounter();
    });

    function updateCounter() {
        const el = document.getElementById('ytcl-count');
        if (el) el.textContent = log.length;
    }

    function setStatus(msg) {
        const el = document.getElementById('ytcl-status');
        if (el) el.textContent = msg;
    }

    // ── Auto-attach polling ───────────────────────────────────────────────────
    // The chat iframe loads after the main page, so we poll until it appears.

    let installed = false;
    let retries   = 0;

    const attachInterval = setInterval(() => {
        if (installObserver()) {
            installed = true;
            setStatus('✅ Logging chat…');
            clearInterval(attachInterval);
        } else if (++retries > 60) {
            // Not a livestream page (or chat disabled)
            setStatus('No live chat found.');
            clearInterval(attachInterval);
        }
    }, 1000);

    // Re-attach when YouTube performs a client-side navigation (SPA)
    new MutationObserver(() => {
        if (!installed) return;
        if (!observer) {
            installed = false;
            setStatus('Reattaching…');
            retries = 0;
            const ri = setInterval(() => {
                if (installObserver()) {
                    installed = true;
                    setStatus('✅ Logging chat…');
                    clearInterval(ri);
                } else if (++retries > 30) {
                    setStatus('No live chat found.');
                    clearInterval(ri);
                }
            }, 1000);
        }
    }).observe(document.body, { childList: true, subtree: false });

})();
