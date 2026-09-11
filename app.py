from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

notes_data = [
        {
            "id": 1,
            "title": "My First Note",
            "content": "This is my first note in the Flask application."
        },
        {
            "id": 2,
            "title": "Learning Flask",
            "content": "Today I learned about routes and templates."
        },
        {
            "id": 3,
            "title": "Project Ideas",
            "content": "Build a useful note-taking application."
        }
]


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/notes")
def notes():
    return render_template("notes.html", notes=notes_data)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/notes/new", methods=["GET", "POST"])
def create_note():
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        new_note = {
            "id": len(notes_data) + 1,
            "title": title,
            "content": content
        }

        notes_data.append(new_note)

        return redirect(url_for("notes"))

    return render_template("create_note.html")
       

if __name__ == "__main__":
    app.run(debug=True)


