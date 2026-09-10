from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/notes")
def notes():

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

    return render_template("notes.html", notes=notes_data)

@app.route("/about")
def about():
    return render_template("about.html")


if __name__ == "__main__":
    app.run(debug=True)


