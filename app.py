from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return "<b>Welcome to My Notes App</b>"


@app.route("/notes")
def notes():
    return "My Notes"

@app.route("/about")
def about():
    return "About My Notes App"



if __name__ == "__main__":
    app.run(debug=True)


