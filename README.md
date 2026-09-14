# Nocturne Studio

A dark, slightly gothic Flask photo-delivery app for creating private client collections and sharing them with a link.

## Run locally

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
```

Then open <http://127.0.0.1:5000>. Create a collection, add multiple images, and use **Copy share link** from the collection view.

Collections and image metadata are stored in `photos.db`; uploaded files are stored in `static/uploads/`.
