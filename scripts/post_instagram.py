"""Postet den nächsten Carousel aus posts/queue.json auf Instagram (Meta Graph API).

Ablauf pro Lauf:
  1. Nächsten unveröffentlichten Post wählen. Nie zweimal hintereinander dasselbe Thema.
  2. Für jede Slide einen Carousel-Item-Container anlegen (Bild über öffentliche GitHub-URL).
  3. Carousel-Container mit Caption anlegen, warten bis FINISHED, veröffentlichen.
  4. In state/published.json eintragen (der Workflow committet die Datei).

Umgebungsvariablen:
  IG_USER_ID        Instagram-Business-Account-ID
  IG_ACCESS_TOKEN   langlebiger Token mit instagram_content_publish
  IMAGE_BASE_URL    z. B. https://raw.githubusercontent.com/<owner>/<repo>/main/posts
  GRAPH_VERSION     optional, Standard v23.0
  DRY_RUN=1         nichts posten, nur zeigen, was passieren würde
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUE = os.path.join(ROOT, "posts", "queue.json")
STATE = os.path.join(ROOT, "state", "published.json")
# Facebook-Login-Token (Page-Token, beginnt meist mit "EAA"): graph.facebook.com
# Instagram-Login-Token (beginnt mit "IG"): graph.instagram.com
_token = os.environ.get("IG_ACCESS_TOKEN", "")
_host = os.environ.get("GRAPH_HOST") or ("graph.instagram.com" if _token.startswith("IG") else "graph.facebook.com")
GRAPH = f"https://{_host}/" + os.environ.get("GRAPH_VERSION", "v23.0")


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def pick_next(posts, published):
    done = {p["id"] for p in published}
    open_posts = [p for p in posts if p["id"] not in done]
    if not open_posts:
        return None
    last_theme = published[-1]["theme"] if published else None
    for p in open_posts:
        if p["theme"] != last_theme:
            return p
    return open_posts[0]


def api(method, path, params):
    data = urllib.parse.urlencode(params).encode()
    url = f"{GRAPH}/{path}"
    if method == "GET":
        url += "?" + data.decode()
        data = None
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise SystemExit(f"Graph API Fehler {e.code} bei {path}: {body}")


def wait_finished(container_id, token, tries=20):
    for _ in range(tries):
        status = api("GET", container_id, {"fields": "status_code", "access_token": token}).get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            raise SystemExit(f"Container {container_id} Status {status}")
        time.sleep(5)
    raise SystemExit(f"Container {container_id} wurde nicht rechtzeitig fertig")


def main():
    queue = load(QUEUE)
    state = load(STATE)
    post = pick_next(queue["posts"], state["published"])
    if post is None:
        print("Warteschlange leer: keine Posts mehr. Neue Posts in posts/queue.json eintragen.")
        return

    base = os.environ.get("IMAGE_BASE_URL", "").rstrip("/")
    images = [f"{base}/{post['id']}/{i}.png" for i in range(1, post["slide_count"] + 1)]
    print(f"Nächster Post: {post['id']} (Thema {post['theme']} {post['theme_name']}), {len(images)} Slides")

    if os.environ.get("DRY_RUN") == "1":
        for u in images:
            print("  Bild:", u)
        print("  Caption:", post["caption"].splitlines()[0], "...")
        print("DRY_RUN: nichts gepostet.")
        return

    user, token = os.environ["IG_USER_ID"], os.environ["IG_ACCESS_TOKEN"]
    if not base:
        raise SystemExit("IMAGE_BASE_URL fehlt")

    children = []
    for u in images:
        res = api("POST", f"{user}/media", {"image_url": u, "is_carousel_item": "true", "access_token": token})
        children.append(res["id"])
    for c in children:
        wait_finished(c, token)

    carousel = api("POST", f"{user}/media", {
        "media_type": "CAROUSEL", "children": ",".join(children),
        "caption": post["caption"], "access_token": token,
    })["id"]
    wait_finished(carousel, token)
    media_id = api("POST", f"{user}/media_publish", {"creation_id": carousel, "access_token": token})["id"]

    state["published"].append({
        "id": post["id"], "theme": post["theme"], "media_id": media_id,
        "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    })
    save(STATE, state)
    print(f"Veröffentlicht: {post['id']} -> media {media_id}")


if __name__ == "__main__":
    sys.exit(main())
