from pathlib import Path
import secrets
import sqlite3
from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
DATABASE = BASE_DIR / "photos.db"
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}

app = Flask(__name__)
app.config["SECRET_KEY"] = secrets.token_hex(16)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024 * 1024
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS shoots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                client TEXT NOT NULL,
                slug TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shoot_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                original_name TEXT NOT NULL,
                uploaded_at TEXT NOT NULL,
                FOREIGN KEY (shoot_id) REFERENCES shoots (id) ON DELETE CASCADE
            );
            """
        )


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def unique_slug():
    return secrets.token_urlsafe(6).lower().replace("_", "-").replace("/", "-")


def find_shoot(slug):
    with get_db() as db:
        return db.execute("SELECT * FROM shoots WHERE slug = ?", (slug,)).fetchone()


def photos_for(shoot_id):
    with get_db() as db:
        return db.execute(
            "SELECT * FROM photos WHERE shoot_id = ? ORDER BY id DESC", (shoot_id,)
        ).fetchall()


@app.context_processor
def inject_globals():
    with get_db() as db:
        shoot_count = db.execute("SELECT COUNT(*) FROM shoots").fetchone()[0]
        photo_count = db.execute("SELECT COUNT(*) FROM photos").fetchone()[0]
    return {"shoot_count": shoot_count, "photo_count": photo_count}


@app.route("/")
def index():
    with get_db() as db:
        shoots = db.execute(
            """
            SELECT s.*, COUNT(p.id) AS photo_count,
                   (SELECT filename FROM photos WHERE shoot_id = s.id ORDER BY id DESC LIMIT 1) AS cover
            FROM shoots s LEFT JOIN photos p ON s.id = p.shoot_id
            GROUP BY s.id ORDER BY s.id DESC
            """
        ).fetchall()
    return render_template("index.html", shoots=shoots)


@app.route("/new", methods=["GET", "POST"])
def new_shoot():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        client = request.form.get("client", "").strip()
        files = request.files.getlist("photos")
        valid_files = [file for file in files if file and allowed_file(file.filename)]

        if not name or not client:
            flash("Add a shoot name and client name to continue.", "error")
            return render_template("new_shoot.html")
        if not valid_files:
            flash("Choose at least one JPG, PNG, WEBP, or GIF image.", "error")
            return render_template("new_shoot.html")

        slug = unique_slug()
        while find_shoot(slug):
            slug = unique_slug()
        timestamp = datetime.utcnow().isoformat(timespec="seconds")
        with get_db() as db:
            shoot_id = db.execute(
                "INSERT INTO shoots (name, client, slug, created_at) VALUES (?, ?, ?, ?)",
                (name, client, slug, timestamp),
            ).lastrowid
            for file in valid_files:
                original = secure_filename(file.filename)
                stored = f"{secrets.token_hex(10)}-{original}"
                file.save(UPLOAD_DIR / stored)
                db.execute(
                    "INSERT INTO photos (shoot_id, filename, original_name, uploaded_at) VALUES (?, ?, ?, ?)",
                    (shoot_id, stored, original, timestamp),
                )
        flash("Your gallery is ready to share.", "success")
        return redirect(url_for("gallery", slug=slug))

    return render_template("new_shoot.html")


@app.route("/gallery/<slug>")
def gallery(slug):
    shoot = find_shoot(slug)
    if not shoot:
        return render_template("not_found.html"), 404
    return render_template("gallery.html", shoot=shoot, photos=photos_for(shoot["id"]), owner_view=True)


@app.route("/share/<slug>")
def shared_gallery(slug):
    shoot = find_shoot(slug)
    if not shoot:
        return render_template("not_found.html"), 404
    return render_template("gallery.html", shoot=shoot, photos=photos_for(shoot["id"]), owner_view=False)


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


@app.errorhandler(413)
def too_large(_error):
    flash("That upload is too large. Please keep the total under 64 MB.", "error")
    return redirect(url_for("new_shoot"))


init_db()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=6969)
