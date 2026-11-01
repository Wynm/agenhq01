# AgenHQ Auto-Video

Daily short vertical videos (Arabic by default) about tech, AI, phone tips, legit online income and fun tech facts,
fully on GitHub Actions, using only free tools:

`Gemini (script) → edge-tts (voice) → Pexels (stock footage) → ffmpeg (1080x1920 + Arabic captions) → GitHub Release → publisher (Postiz / YouTube / webhook)`

📖 **الشرح الكامل بالدارجة:** [docs/README-darija.md](docs/README-darija.md)

## Quick start
- Secrets: `GEMINI_API_KEY` (aistudio.google.com/apikey), `PEXELS_API_KEY` (pexels.com/api). Both optional: without them a mock script + gradient backgrounds are used.
- Run: **Actions → Daily video → Run workflow** (also runs daily by cron).
- Publishing is OFF until you set the repo variable `PUBLISHERS` (e.g. `postiz`) and its secrets.

## Local run
```bash
sudo apt install ffmpeg
pip install -r requirements.txt
python -m autovid.main make                      # -> out/<id>/video.mp4 + meta.json
python -m autovid.main publish --meta out/<id>/meta.json --video-url URL
python -m autovid.main channels                  # list Postiz channel ids
```

## Publishers (`autovid/publishers/`)
| name | env | status |
|---|---|---|
| `postiz` (primary) | `POSTIZ_API_KEY`, opt. `POSTIZ_API_URL`, `POSTIZ_INTEGRATIONS`, `POSTIZ_POST_TYPE` | implemented per Postiz public API docs (tested against a mock) |
| `youtube` | `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN` | implemented (resumable upload) |
| `webhook` | `POST_WEBHOOK_URL`, opt. `POST_WEBHOOK_TOKEN` | implemented |
| `mixpost` | `MIXPOST_URL`, `MIXPOST_TOKEN`, `MIXPOST_WORKSPACE`, `MIXPOST_ACCOUNTS` | untested stub (needs Mixpost Pro API) |

Post only to your own accounts. Stock footage credits are written to `meta.json` and the release notes.
Fonts: Cairo, Noto Sans/Naskh Arabic (SIL Open Font License, see `assets/fonts/OFL.txt`).
