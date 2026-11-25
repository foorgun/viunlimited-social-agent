"""Rendert die Carousel-Artboards aus canvas/ in einzelne PNG-Slides (1080x1350).

Jede .dc.html im Canvas ist ein Streifen aus N Slides nebeneinander.
Das Skript baut daraus pro Slide eine schlichte HTML-Seite und macht
mit Chrome (headless) einen Screenshot.

Aufruf:  python3 scripts/render.py            # alle Posts aus posts/queue.json
         python3 scripts/render.py w1-di      # nur einen Post
"""
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
W, H = 1080, 1350


def standalone(dc_html: str) -> str:
    """Macht aus einer .dc.html eine normale HTML-Seite ohne Canvas-Runtime."""
    helmet = re.search(r"<helmet>(.*?)</helmet>", dc_html, re.S)
    body = re.search(r"</helmet>(.*?)</x-dc>", dc_html, re.S)
    if not helmet or not body:
        raise ValueError("Unerwartetes Artboard-Format")
    head = helmet.group(1)
    # Uploads im Canvas (/_blob/<id>) zeigen lokal auf assets/ (z. B. das Logo)
    logo = "file://" + os.path.join(ROOT, "assets", "logo.png")
    body_html = re.sub(r"/_blob/[0-9a-f]+", logo, body.group(1))
    return (
        "<!doctype html><html lang='de'><head><meta charset='utf-8'>"
        f"{head}<style>html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden;background:#141215}}"
        "#strip{position:absolute;top:0;left:0}</style></head>"
        f"<body><div id='strip'>{body_html}</div></body></html>"
    )


def render_post(post: dict) -> None:
    src = os.path.join(ROOT, "canvas", post["canvas_file"])
    with open(src, encoding="utf-8") as f:
        page = standalone(f.read())
    out_dir = os.path.join(ROOT, "posts", post["id"])
    os.makedirs(out_dir, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(post["slide_count"]):
            html_path = os.path.join(tmp, f"slide{i + 1}.html")
            shifted = page.replace("#strip{position:absolute;top:0;left:0}",
                                   f"#strip{{position:absolute;top:0;left:{-W * i}px}}")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(shifted)
            png = os.path.join(out_dir, f"{i + 1}.png")
            subprocess.run([
                CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                f"--window-size={W},{H}", "--force-device-scale-factor=1",
                "--virtual-time-budget=6000", f"--screenshot={png}",
                "file://" + html_path,
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("  ", os.path.relpath(png, ROOT))


def main() -> None:
    with open(os.path.join(ROOT, "posts", "queue.json"), encoding="utf-8") as f:
        queue = json.load(f)["posts"]
    only = set(sys.argv[1:])
    for post in queue:
        if only and post["id"] not in only:
            continue
        print(post["id"])
        render_post(post)


if __name__ == "__main__":
    main()
