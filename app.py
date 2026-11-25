
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import sqlite3
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "project4_secret_key"

# Project folders
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DATABASE = os.path.join(BASE_DIR, "videos.db")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm"}


# Check video extension
def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# Connect to database
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# Create database table automatically
def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            filename TEXT NOT NULL,
            scheduled_at TEXT,
            status TEXT NOT NULL,
            youtube_url TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


# Dashboard
@app.route("/")
def dashboard():
    conn = get_db()

    videos = conn.execute(
        "SELECT * FROM videos ORDER BY id DESC"
    ).fetchall()

    total = conn.execute(
        "SELECT COUNT(*) FROM videos"
    ).fetchone()[0]

    scheduled = conn.execute(
        "SELECT COUNT(*) FROM videos WHERE status = 'Scheduled'"
    ).fetchone()[0]

    published = conn.execute(
        "SELECT COUNT(*) FROM videos WHERE status = 'Published'"
    ).fetchone()[0]

    pending = conn.execute(
        "SELECT COUNT(*) FROM videos WHERE status = 'Pending'"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        videos=videos,
        total=total,
        scheduled=scheduled,
        published=published,
        pending=pending
    )


# Upload video
@app.route("/upload", methods=["GET", "POST"])
def upload():

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        description = request.form.get("description", "")
        scheduled_at = request.form.get("scheduled_at", "")
        video = request.files.get("video")

        if not title:
            flash("Please enter video title.")
            return redirect(url_for("upload"))

        if not video or video.filename == "":
            flash("Please select a video.")
            return redirect(url_for("upload"))

        if not allowed_file(video.filename):
            flash("Only MP4, MOV, AVI, MKV and WEBM videos are allowed.")
            return redirect(url_for("upload"))

        original_name = secure_filename(video.filename)
        extension = original_name.rsplit(".", 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{extension}"

        video.save(os.path.join(UPLOAD_FOLDER, filename))

        if scheduled_at:
            try:
                schedule_time = datetime.fromisoformat(scheduled_at)
                if schedule_time > datetime.now():
                    status = "Scheduled"
                else:
                    status = "Pending"
            except ValueError:
                status = "Pending"
                scheduled_at = ""
        else:
            status = "Pending"

        conn = get_db()

        conn.execute("""
            INSERT INTO videos
            (title, description, filename, scheduled_at, status, youtube_url, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            title,
            description,
            filename,
            scheduled_at,
            status,
            "",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()
        conn.close()

        flash("Video uploaded successfully!")
        return redirect(url_for("dashboard"))

    return render_template("upload.html")


# Edit video
@app.route("/edit/<int:video_id>", methods=["GET", "POST"])
def edit(video_id):

    conn = get_db()

    video = conn.execute(
        "SELECT * FROM videos WHERE id = ?",
        (video_id,)
    ).fetchone()

    if video is None:
        conn.close()
        flash("Video not found.")
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        description = request.form.get("description", "")
        scheduled_at = request.form.get("scheduled_at", "")

        if not title:
            conn.close()
            flash("Title cannot be empty.")
            return redirect(url_for("edit", video_id=video_id))

        if scheduled_at:
            try:
                schedule_time = datetime.fromisoformat(scheduled_at)
                status = (
                    "Scheduled"
                    if schedule_time > datetime.now()
                    else "Pending"
                )
            except ValueError:
                status = "Pending"
                scheduled_at = ""
        else:
            status = "Pending"

        conn.execute("""
            UPDATE videos
            SET title = ?, description = ?, scheduled_at = ?, status = ?
            WHERE id = ?
        """, (
            title,
            description,
            scheduled_at,
            status,
            video_id
        ))

        conn.commit()
        conn.close()

        flash("Video updated successfully!")
        return redirect(url_for("dashboard"))

    conn.close()
    return render_template("edit.html", video=video)


# Delete video
@app.route("/delete/<int:video_id>", methods=["POST"])
def delete(video_id):

    conn = get_db()

    video = conn.execute(
        "SELECT * FROM videos WHERE id = ?",
        (video_id,)
    ).fetchone()

    if video:
        file_path = os.path.join(UPLOAD_FOLDER, video["filename"])

        if os.path.exists(file_path):
            os.remove(file_path)

        conn.execute(
            "DELETE FROM videos WHERE id = ?",
            (video_id,)
        )

        conn.commit()
        flash("Video deleted successfully!")

    conn.close()

    return redirect(url_for("dashboard"))


# Preview uploaded video
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# Start application
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
