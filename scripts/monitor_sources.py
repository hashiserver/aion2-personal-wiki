"""Daily, non-destructive monitoring for public Global AION2 sources.

Only records HTTP metadata and change signals. Never silently rewrites verified game facts.
"""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "monitor_sources.json"
OUTPUT = ROOT / "data" / "source_monitor.json"
AGENT = "AION2PortalSourceMonitor/1.0 (+https://github.com/hashiserver/aion2-personal-wiki)"

def check_source(source, previous):
    url = source["url"]
    if not url.startswith("https://"):
        raise ValueError("HTTPS required")
    old = previous.get("sources", {}).get(source["id"], {})
    headers = {"User-Agent": AGENT, "Accept": "text/html,application/json,application/xml,text/xml;q=0.9"}
    if old.get("etag"):
        headers["If-None-Match"] = old["etag"]
    if old.get("last_modified"):
        headers["If-Modified-Since"] = old["last_modified"]
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            # Bound memory and never persist/reproduce copyrighted page contents.
            content = response.read(2_000_001)
            if len(content) > 2_000_000:
                raise ValueError("response over 2 MB; skipped")
            digest = hashlib.sha256(content).hexdigest()
            return {"status": "changed" if old.get("sha256") != digest else "unchanged",
                    "sha256": digest, "etag": response.headers.get("ETag"),
                    "last_modified": response.headers.get("Last-Modified"),
                    "http_status": response.status, "url": url}
    except urllib.error.HTTPError as e:
        if e.code == 304 and old.get("sha256"):
            return dict(old, status="unchanged", http_status=304)
        raise

def run():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    previous = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    sources = dict(previous.get("sources", {}))
    stamp = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    for source in catalog:
        sid = source["id"]
        try:
            record = check_source(source, previous)
            record.update(region=source["region"], classification=source["classification"],
                          checked_at=stamp, error=None)
            sources[sid] = record
        except (OSError, ValueError, urllib.error.URLError) as exc:
            # Preserve last good digest and explicitly show staleness/failure.
            old = dict(sources.get(sid, {}))
            old.update(url=source["url"], region=source["region"],
                       classification=source["classification"], status="error",
                       last_attempt_at=stamp, error=str(exc)[:240])
            sources[sid] = old
    result = {"run_at": stamp, "notice": "Monitoring only; changes require human verification before game advice is updated.", "sources": sources}
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k:v["status"] for k,v in sources.items()}, ensure_ascii=False))
if __name__ == "__main__":
    run()
