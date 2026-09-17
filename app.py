from flask import Flask, render_template, request, redirect, url_for, abort, flash
import sqlite3

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
            content TEXT NOT NULL
        )
    """)

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

    connection = get_db_connection()

    if search_query:
        notes_list = connection.execute(
            """
            SELECT * FROM notes
            WHERE LOWER(title) LIKE ?
               OR LOWER(content) LIKE ?
            ORDER BY id DESC
            """,
            (f"%{search_query}%", f"%{search_query}%")
        ).fetchall()
    else:
        notes_list = connection.execute(
            "SELECT * FROM notes ORDER BY id DESC"
        ).fetchall()

    connection.close()

    return render_template(
        "notes.html",
        notes=notes_list,
        search_query=search_query
    )


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/notes/new", methods=["GET", "POST"])
def create_note():
    if request.method == "POST":
        title = request.form["title"].strip()
        content = request.form["content"].strip()

        if not title or not content:
            return render_template(
                "create_note.html",
                error="Title and content are required."
            )

        connection = get_db_connection()

        connection.execute(
            "INSERT INTO notes (title, content) VALUES (?, ?)",
            (title, content)
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

        if not title or not content:
            return render_template(
                "edit_note.html",
                note=note,
                error="Title and content are required."
            )

        connection = get_db_connection()

        connection.execute(
            """
            UPDATE notes
            SET title = ?, content = ?
            WHERE id = ?
            """,
            (title, content, note_id)
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