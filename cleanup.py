#!/usr/bin/env python3
"""
Gmail cleanup script — rule-based, zero AI/tokens.
Moves matching emails to trash and unsubscribes from mailing lists.

Setup (once):
  pip install google-api-python-client google-auth-oauthlib requests
  # Put credentials.json from Google Cloud Console next to this script
  python cleanup.py --dry-run          # preview first
  python cleanup.py                    # trash + unsubscribe
  python cleanup.py --no-unsubscribe   # just trash, skip unsubscribe
"""

import argparse
import os
import pickle
import re
import socket
import ssl
import time

import requests
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

_NETWORK_ERRORS = (
    socket.timeout, socket.gaierror,
    ssl.SSLError, ConnectionResetError, ConnectionError,
    requests.exceptions.ConnectionError, requests.exceptions.Timeout,
    OSError,
)

def _retry(fn, *args, retries=5, **kwargs):
    delay = 5
    for attempt in range(retries):
        try:
            return fn(*args, **kwargs)
        except ssl.CertificateError:
            raise
        except _NETWORK_ERRORS as e:
            if attempt == retries - 1:
                raise
            print(f"  [network error] {e} — повтор через {delay}с...")
            time.sleep(delay)
            delay = min(delay * 2, 60)

# ─── CONFIG ──────────────────────────────────────────────────────────────────

SEARCH_QUERIES = [
    "category:promotions in:inbox",
    "category:updates in:inbox",
    "in:spam",
    # "category:social in:inbox",
]

TRASH_SENDERS = [
    "news.ozon.ru",
    "nvgaming.nvidia.com",
    "team.brain.fm",
    "news.ostrovok.ru",
    "okx.com",
    "mail.timepad.ru",
    "digital.alfabank.ru",
    "newsletter.trip.com",
    "skillbox.ru",
    "email.epicgames.com",
    "mail.5ka.ru",
    "geeksforgeeks.org",
    "rustore.ru",
]

SAFETY_KEYWORDS = [
    "invoice", "receipt", "order", "shipping", "payment",
    "booking", "confirmation", "reservation", "ticket",
    "password reset", "verification", "2fa", "security alert",
    "счёт", "оплата", "заказ", "доставка", "подтверждение",
    "накладная", "бронирование", "билет", "код подтверждения",
    # чеки и финансовые операции
    "чек", "квитанция", "квитанции", "транзакция", "перевод",
    "списание", "зачисление", "выписка", "платёж совершён",
]

# Домены, письма с которых никогда не удаляются (чеки, банки, платёжки)
SAFE_SENDERS = [
    # добавь сюда домены, с которых приходят важные чеки/выписки
]

# ─────────────────────────────────────────────────────────────────────────────

SCOPES = ["https://www.googleapis.com/auth/gmail.modify", "https://www.googleapis.com/auth/gmail.send"]
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token.pickle")
CREDS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")


def get_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDS_FILE):
                print("ERROR: credentials.json not found.")
                print("  1. Go to https://console.cloud.google.com/")
                print("  2. Create project → Enable Gmail API → Create OAuth credentials (Desktop app)")
                print("  3. Download as credentials.json and place next to this script")
                raise SystemExit(1)
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)
    return build("gmail", "v1", credentials=creds)


def is_safe(subject: str, sender: str = "") -> bool:
    subject_lower = subject.lower()
    if any(kw in subject_lower for kw in SAFETY_KEYWORDS):
        return True
    sender_lower = sender.lower()
    return any(domain in sender_lower for domain in SAFE_SENDERS)


def search_threads(service, query: str):
    threads = []
    page_token = None
    while True:
        kwargs = {"userId": "me", "q": query, "maxResults": 500}
        if page_token:
            kwargs["pageToken"] = page_token
        resp = _retry(service.users().threads().list(**kwargs).execute)
        threads.extend(resp.get("threads", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return threads


def get_thread_info(service, thread_id: str):
    """Returns (subject, sender, unsub_mailto, unsub_url, unsub_one_click)."""
    thread = _retry(
        service.users().threads().get(
            userId="me", id=thread_id, format="metadata",
            metadataHeaders=["Subject", "From", "List-Unsubscribe", "List-Unsubscribe-Post"]
        ).execute
    )
    subject = sender = unsub_header = ""
    unsub_one_click = False
    for msg in thread.get("messages", [])[:1]:
        for h in msg.get("payload", {}).get("headers", []):
            name = h["name"].lower()
            val = h["value"]
            if name == "subject":
                subject = val
            elif name == "from":
                sender = val
            elif name == "list-unsubscribe":
                unsub_header = val
            elif name == "list-unsubscribe-post":
                # RFC 8058: presence means one-click POST is supported
                unsub_one_click = True

    mailto, url = parse_unsub_header(unsub_header)
    return subject, sender, mailto, url, unsub_one_click


def parse_unsub_header(header: str):
    """Extract (mailto_addr, https_url) from List-Unsubscribe header."""
    mailto = url = None
    for part in re.findall(r"<([^>]+)>", header):
        if part.startswith("mailto:") and mailto is None:
            addr = part[7:]
            mailto = addr.split("?")[0].strip()
        elif part.startswith("http") and url is None:
            url = part.strip()
    return mailto, url


def unsubscribe(url: str, one_click: bool, dry_run: bool) -> str:
    if dry_run:
        if url:
            return f"would {'POST' if one_click else 'GET'} → {url[:60]}"
        return "no unsub link"

    if url:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            if one_click:
                _retry(requests.post, url, data={"List-Unsubscribe": "One-Click"}, headers=headers, timeout=10)
            else:
                _retry(requests.get, url, headers=headers, timeout=10)
            return f"{'POST' if one_click else 'GET'} → {url[:60]}"
        except Exception as e:
            return f"http failed: {e}"

    return "no unsub header"


def trash_thread(service, thread_id: str):
    _retry(service.users().threads().trash(userId="me", id=thread_id).execute)


def process_thread(service, tid: str, dry_run: bool, do_unsub: bool):
    """Returns (action, unsub_status) where action is 'trashed'|'skipped'."""
    subject, sender, mailto, url, one_click = get_thread_info(service, tid)

    if is_safe(subject, sender):
        label = sender.split("<")[0].strip()[:20]
        print(f"  SKIP  (safety): [{label}] {subject[:60]}")
        return "skipped", None

    label = sender.split("<")[0].strip()[:20]
    unsub_status = ""

    if do_unsub and url:
        unsub_status = unsubscribe(url, one_click, dry_run)
        print(f"  TRASH + UNSUB: [{label}] {subject[:55]}")
        print(f"    unsub: {unsub_status}")
    else:
        print(f"  TRASH: [{label}] {subject[:60]}")

    if not dry_run:
        trash_thread(service, tid)

    return "trashed", unsub_status


def run(dry_run: bool, do_unsub: bool):
    service = get_service()
    mode = "DRY RUN" if dry_run else "LIVE"
    unsub_note = " + unsubscribe" if do_unsub else ""
    print(f"Mode: {mode}{unsub_note}\n")

    seen_ids = set()
    total_trashed = total_skipped = total_unsubbed = 0

    for query in SEARCH_QUERIES:
        print(f"[Query] {query}")
        threads = search_threads(service, query)
        print(f"  Found {len(threads)} threads")
        for t in threads:
            tid = t["id"]
            if tid in seen_ids:
                continue
            seen_ids.add(tid)
            action, unsub = process_thread(service, tid, dry_run, do_unsub)
            if action == "trashed":
                total_trashed += 1
                if unsub and "failed" not in unsub and "no unsub" not in unsub:
                    total_unsubbed += 1
            else:
                total_skipped += 1
        print()

    print("[Senders] Checking known promo senders...")
    for domain in TRASH_SENDERS:
        threads = search_threads(service, f"from:{domain} in:inbox")
        for t in threads:
            tid = t["id"]
            if tid in seen_ids:
                continue
            seen_ids.add(tid)
            action, unsub = process_thread(service, tid, dry_run, do_unsub)
            if action == "trashed":
                total_trashed += 1
                if unsub and "failed" not in unsub and "no unsub" not in unsub:
                    total_unsubbed += 1
            else:
                total_skipped += 1

    print("\n" + "━" * 50)
    print(f"Done!  Trashed: {total_trashed}  |  Unsubscribed: {total_unsubbed}  |  Skipped: {total_skipped}")
    if dry_run:
        print("(dry-run — nothing was actually changed)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gmail rule-based cleanup with unsubscribe")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, don't trash or unsubscribe")
    parser.add_argument("--no-unsubscribe", action="store_true", help="Trash only, skip unsubscribe")
    args = parser.parse_args()
    run(dry_run=args.dry_run, do_unsub=not args.no_unsubscribe)
