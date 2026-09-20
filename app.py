from flask import Flask, render_template, request, redirect, url_for, abort, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)

app.secret_key = "your_secret_key"

DATABASE = "notes.db"


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'General',
            created_at TEXT NOT NULL
        )
    """)

    columns = connection.execute(
        "PRAGMA table_info(notes)"
    ).fetchall()

    column_names = [column["name"] for column in columns]

    if "category" not in column_names:
        connection.execute(
            "ALTER TABLE notes ADD COLUMN category TEXT NOT NULL DEFAULT 'General'"
        )

    if "created_at" not in column_names:
        connection.execute(
            "ALTER TABLE notes ADD COLUMN created_at TEXT NOT NULL DEFAULT ''"
        )

    connection.commit()
    connection.close()


def find_note(note_id):
    connection = get_db_connection()

    note = connection.execute(
        "SELECT * FROM notes WHERE id = ?",
        (note_id,)
    ).fetchone()

    connection.close()

    return note


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/notes")
def notes():
    search_query = request.args.get("search", "").strip().lower()
    selected_category = request.args.get("category", "").strip()
    sort_order = request.args.get("sort", "newest")

    connection = get_db_connection()

    query = "SELECT * FROM notes WHERE 1=1"
    parameters = []

    # Search title, content, or category
    if search_query:
        query += """
            AND (
                LOWER(title) LIKE ?
                OR LOWER(content) LIKE ?
                OR LOWER(category) LIKE ?
            )
        """

        search_value = f"%{search_query}%"
        parameters.extend([
            search_value,
            search_value,
            search_value
        ])

    # Filter by category
    if selected_category:
        query += " AND category = ?"
        parameters.append(selected_category)

    # Sort results
    if sort_order == "oldest":
        query += " ORDER BY id ASC"
    else:
        query += " ORDER BY id DESC"

    notes_list = connection.execute(
        query,
        parameters
    ).fetchall()

    # Count all notes
    total_notes = connection.execute(
        "SELECT COUNT(*) AS total FROM notes"
    ).fetchone()["total"]

    # Count Study notes
    study_notes = connection.execute(
        "SELECT COUNT(*) AS total FROM notes WHERE category = ?",
        ("Study",)
    ).fetchone()["total"]

    # Count Work notes
    work_notes = connection.execute(
        "SELECT COUNT(*) AS total FROM notes WHERE category = ?",
        ("Work",)
    ).fetchone()["total"]

    

    connection.close()

    return render_template(
        "notes.html",
        notes=notes_list,
        search_query=search_query,
        selected_category=selected_category,
        sort_order=sort_order,
        total_notes=total_notes,
        study_notes=study_notes,
        work_notes=work_notes
    )


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/notes/new", methods=["GET", "POST"])
def create_note():
    if request.method == "POST":
        title = request.form["title"].strip()
        content = request.form["content"].strip()
        category = request.form["category"].strip()

        if not title or not content or not category:
            return render_template(
                "create_note.html",
                error="Title, content, and category are required."
            )

        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        connection = get_db_connection()

        connection.execute(
            """
            INSERT INTO notes (title, content, category, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (title, content, category, created_at)
        )

        connection.commit()
        connection.close()

        flash("Note created successfully!", "success")

        return redirect(url_for("notes"))

    return render_template("create_note.html")


@app.route("/notes/<int:note_id>")
def view_note(note_id):
    note = find_note(note_id)

    if note is None:
        abort(404)

    return render_template("view_note.html", note=note)


@app.route("/notes/<int:note_id>/edit", methods=["GET", "POST"])
def edit_note(note_id):
    note = find_note(note_id)

    if note is None:
        abort(404)

    if request.method == "POST":
        title = request.form["title"].strip()
        content = request.form["content"].strip()
        category = request.form["category"].strip()

        if not title or not content or not category:
            return render_template(
                "edit_note.html",
                note=note,
                error="Title, content, and category are required."
            )

        connection = get_db_connection()

        connection.execute(
            """
            UPDATE notes
            SET title = ?, content = ?, category = ?
            WHERE id = ?
            """,
            (title, content, category, note_id)
        )

        connection.commit()
        connection.close()

        flash("Note updated successfully!", "success")

        return redirect(url_for("view_note", note_id=note_id))

    return render_template("edit_note.html", note=note)


@app.route("/notes/<int:note_id>/delete", methods=["POST"])
def delete_note(note_id):
    note = find_note(note_id)

    if note is None:
        abort(404)

    connection = get_db_connection()

    connection.execute(
        "DELETE FROM notes WHERE id = ?",
        (note_id,)
    )

    connection.commit()
    connection.close()

    flash("Note deleted successfully!", "success")

    return redirect(url_for("notes"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)