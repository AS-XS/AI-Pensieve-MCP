import json
import re
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

from .db import initialize
from .importing import account_id, conversation_id, upsert_memory, upsert_message


ACTIVITY_DATE = re.compile(
    r"\b[A-Z][a-z]{2} \d{1,2}, \d{4}, \d{1,2}:\d{2}:\d{2} [AP]M CST\b"
)
SESSION_GAP_SECONDS = 60 * 60


class ActivityParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.current = None
        self.entries = []
        self.skip_link = False

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "div":
            self.depth += 1
            classes = set(attributes.get("class", "").split())
            excluded = {"mdl-typography--text-right", "mdl-typography--caption"}
            if "content-cell" in classes and not classes & excluded:
                self.current = {"depth": self.depth, "chunks": [self._chunk()]}
        elif self.current and tag == "br":
            self.current["chunks"].append(self._chunk())
        elif self.current and tag == "a":
            url = urlparse(attributes.get("href", ""))
            if url.netloc == "myaccount.google.com":
                self.current["chunks"][-1]["control"] = True
            self.skip_link = not url.scheme and not url.netloc

    def handle_startendtag(self, tag, attrs):
        if self.current and tag == "br":
            self.current["chunks"].append(self._chunk())

    def handle_data(self, data):
        if self.current and not self.skip_link and data.strip():
            self.current["chunks"][-1]["text"].append(data)

    def handle_endtag(self, tag):
        if tag == "a":
            self.skip_link = False
        if tag != "div":
            return
        if self.current and self.depth == self.current["depth"]:
            entry = self._entry(self.current["chunks"])
            if entry:
                self.entries.append(entry)
            self.current = None
        self.depth -= 1

    @staticmethod
    def _chunk():
        return {"text": [], "control": False}

    @staticmethod
    def _entry(chunks):
        texts = [" ".join(" ".join(chunk["text"]).split()) for chunk in chunks]
        date_index = next((i for i, text in enumerate(texts) if ACTIVITY_DATE.search(text)), None)
        if date_index is None:
            return None
        date = ACTIVITY_DATE.search(texts[date_index]).group()
        prompt = "\n".join(
            text for text, chunk in zip(texts[:date_index], chunks[:date_index])
            if text and not chunk["control"]
        )
        response = "\n".join(text for text in texts[date_index + 1:] if text)
        return {"date": date, "prompt": prompt, "response": response}


def activity_time(value):
    parsed = datetime.strptime(value, "%b %d, %Y, %I:%M:%S %p CST")
    return parsed.replace(tzinfo=timezone(-timedelta(hours=6))).timestamp()


def import_activity(connection, source, account):
    parser = ActivityParser()
    parser.feed(source.read_text(encoding="utf-8-sig"))
    source_account = account_id(connection, "gemini", account)
    entries = sorted(
        (activity_time(entry["date"]), entry) for entry in parser.entries
    )
    sessions = []
    for created_at, entry in entries:
        if not sessions or created_at - sessions[-1][-1][0] > SESSION_GAP_SECONDS:
            sessions.append([])
        sessions[-1].append((created_at, entry))

    connection.execute(
        "DELETE FROM conversations WHERE account_id = ? AND "
        "(source_id LIKE 'activity:%' OR source_id LIKE 'activity-session:%')",
        (source_account,),
    )
    node_count = 0
    for session in sessions:
        started_at, ended_at = session[0][0], session[-1][0]
        key = conversation_id(
            connection, source_account, f"activity-session:{int(started_at)}", source,
            "Gemini activity session", started_at, ended_at, "activity_session",
        )
        parent = None
        for created_at, entry in session:
            user_id = f"activity:{entry['date']}:user"
            upsert_message(
                connection, key, user_id, None, parent,
                "user", entry["prompt"], created_at,
            )
            node_count += 1
            parent = user_id
            if entry["response"]:
                assistant_id = f"activity:{entry['date']}:assistant"
                upsert_message(
                    connection, key, assistant_id, None, parent,
                    "assistant", entry["response"], created_at,
                )
                node_count += 1
                parent = assistant_id

    return {"conversations": len(sessions), "nodes": node_count}


def import_notebook(connection, source, account):
    data = json.loads(source.read_text(encoding="utf-8-sig"))
    created_at = data["metadata"]["createTime"]
    source_account = account_id(connection, "notebooklm", account)
    upsert_memory(
        connection, source_account, f"notebook:{created_at}", source,
        "notebook", data["title"], data["title"], created_at,
    )
    return {"memories": 1}


def import_file(connection, source, account="default"):
    source = Path(source)
    initialize(connection)
    with connection:
        if source.suffix == ".json":
            return import_notebook(connection, source, account)
        return import_activity(connection, source, account)
