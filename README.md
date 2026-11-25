# ViUnlimited Social Agent

Postet zweimal pro Woche (Di + Fr, 08:00 Uhr Winterzeit) automatisch einen Carousel auf
Instagram @vi_unlimited_gym. Gleiche Bauweise wie der foorgun.ai-Agent:
GitHub Action + Meta Graph API, fertig gerenderte Slides im Repo, Status im Repo.

## Aufbau

| Pfad | Inhalt |
|---|---|
| `canvas/*.dc.html` | Quellen aus dem Design-Canvas, je Datei ein Carousel mit 5 Slides nebeneinander |
| `posts/queue.json` | Reihenfolge, Thema (A–E) und Caption jedes Posts |
| `posts/<id>/1–5.png` | Fertige Slides, 1080×1350 |
| `state/published.json` | Was schon veröffentlicht ist (schreibt der Agent selbst) |
| `scripts/render.py` | Canvas → PNG-Slides (lokal, mit Chrome) |
| `scripts/post_instagram.py` | Postet den nächsten Carousel |
| `.github/workflows/post.yml` | Zeitplan, manueller Testlauf, Pause |

Themen: A Einsteiger · B Technik · C Menschen & Erfolge · D Angebot mit Szene · E Mythen & Ausreden.
Zwei gleiche Themen kommen nie direkt hintereinander.

## Einmalige Einrichtung

1. **Instagram-Account:** @vi_unlimited_gym als Business- oder Creator-Account,
   verbunden mit einer Facebook-Seite.
2. **Meta-App** (developers.facebook.com): Produkt „Instagram“ hinzufügen, Rechte
   `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`.
3. **Langlebigen Page-Token** erzeugen und die **Instagram-Business-Account-ID** auslesen
   (wie bei foorgun).
4. **GitHub-Repo** anlegen (öffentlich, damit Instagram die Bilder über
   `raw.githubusercontent.com` abholen kann) und diesen Ordner pushen.
5. **Secrets** im Repo eintragen: `IG_USER_ID`, `IG_ACCESS_TOKEN`.
6. **Testlauf:** Actions → „Instagram posten“ → Run workflow, „Nur testen“ angehakt.
   Danach einmal ohne Haken für den ersten echten Post.

Pause: Repository-Variable `PAUSED` = `true`.
Fehler: GitHub schickt eine Mail, der Post wird beim nächsten Lauf erneut versucht.

## Neue Posts nachlegen

1. Carousels im Canvas gestalten (oder von Claude erstellen lassen).
2. `.dc.html` nach `canvas/` kopieren, Eintrag in `posts/queue.json` ergänzen.
3. `python3 scripts/render.py <id>` rendert die Slides.
4. Committen und pushen. Ist die Warteschlange leer, postet der Agent nichts und meldet das im Log.

Bei 2 Posts pro Woche reichen 8 neue Posts für 4 Wochen.
