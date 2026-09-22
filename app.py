
# នាំចូល Flask និង tools ដែលប្រើសម្រាប់បង្កើត web application។
from flask import Flask, render_template, request, redirect, url_for, abort, flash
# sqlite3 គឺជា module សម្រាប់ធ្វើការជាមួយ SQLite database។
import sqlite3
# datetime ប្រើសម្រាប់យកថ្ងៃ និងម៉ោងបច្ចុប្បន្ន។
from datetime import datetime

# បង្កើត Flask application។ __name__ ជួយ Flask ស្វែងរក files របស់ project។
app = Flask(__name__)

# secret_key ប្រើការពារ session និង flash message។ នៅពេល deploy គួរប្តូរទៅជាតម្លៃសម្ងាត់។
app.secret_key = "your_secret_key"

# variable នេះរក្សាឈ្មោះ file SQLite database របស់ application។
DATABASE = "notes.db"


def get_db_connection():
    # បើក connection ថ្មីទៅកាន់ database។
    connection = sqlite3.connect(DATABASE)
    # ធ្វើឱ្យ row ដែលបានពី database អាចចូលតាមឈ្មោះ column បាន ដូចជា note["title"]។
    connection.row_factory = sqlite3.Row
    # បញ្ជូន connection ទៅ function ដែលហៅវា។
    return connection


def init_db():
    # ភ្ជាប់ទៅ database ដើម្បីបង្កើត tables ដំបូង។
    connection = get_db_connection()

    # បង្កើត table categories បើវាមិនទាន់មាន។
    connection.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)

    # បង្កើត table notes សម្រាប់រក្សាទុក note នីមួយៗ។
    connection.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'General',
            created_at TEXT NOT NULL
        )
    """)

    # បង្កើត list នៃ category លំនាំដើម។
    default_categories = [
        "Study",
        "Work",
        "Personal",
        "Ideas",
        "General"
    ]

    for category_name in default_categories:
        # INSERT OR IGNORE បន្ថែម category លុះត្រាតែឈ្មោះនោះមិនទាន់មានក្នុង database។
        connection.execute(
            """
            INSERT OR IGNORE INTO categories (name)
            VALUES (?)
            """,
            (category_name,)
        )

    # commit រក្សាទុកការកែប្រែទៅក្នុង database ជាអចិន្ត្រៃយ៍។
    connection.commit()
    # បិទ connection បន្ទាប់ពីប្រើរួច។
    connection.close()


def find_note(note_id):
    # បើក connection ដើម្បីស្វែងរក note តាម id។
    connection = get_db_connection()

    # ? ជា placeholder ដែលបញ្ជូន note_id ដោយសុវត្ថិភាពទៅ SQL query។
    note = connection.execute(
        "SELECT * FROM notes WHERE id = ?",
        (note_id,)
    ).fetchone()

    # បិទ connection បន្ទាប់ពីទាញយក note រួច។
    connection.close()

    # បញ្ជូន note មួយ ឬ None បើរកមិនឃើញ។
    return note


def get_all_categories():
    # បើក connection ដើម្បីទាញយក categories ទាំងអស់។
    connection = get_db_connection()

    # ORDER BY name ASC រៀប category តាមអក្សរពី A ទៅ Z។
    categories = connection.execute(
        "SELECT * FROM categories ORDER BY name ASC"
    ).fetchall()

    # បិទ connection បន្ទាប់ពីទាញយកទិន្នន័យរួច។
    connection.close()

    # បញ្ជូន list នៃ categories ទៅកន្លែងដែលហៅ function នេះ។
    return categories


@app.route("/")
def home():
    # route "/" បង្ហាញទំព័រដើម index.html។
    return render_template("index.html")


@app.route("/notes")
def notes():
    # request.args អានតម្លៃពី URL ដូចជា /notes?search=python។
    # strip() ដកចន្លោះខាងមុខ/ក្រោយ និង lower() បម្លែង search ទៅជាអក្សរតូច។
    search_query = request.args.get("search", "").strip().lower()
    selected_category = request.args.get("category", "").strip()
    sort_order = request.args.get("sort", "newest")

    # បើក connection ដើម្បីទាញយក notes ពី database។
    connection = get_db_connection()

    # ចាប់ផ្ដើម SQL query ហើយ parameters រក្សាតម្លៃសម្រាប់ placeholders។
    query = "SELECT * FROM notes WHERE 1=1"
    parameters = []

    # បើមាន search text ស្វែងរកក្នុង title, content ឬ category។
    if search_query:
        query += """
            AND (
                LOWER(title) LIKE ?
                OR LOWER(content) LIKE ?
                OR LOWER(category) LIKE ?
            )
        """

        # % មានន័យថាអាចមានអក្សរផ្សេងទៀតនៅមុខ ឬក្រោយ search text។
        search_value = f"%{search_query}%"

        # បន្ថែមតម្លៃដូចគ្នា 3 ដង សម្រាប់ placeholders 3 ក្នុង query។
        parameters.extend([
            search_value,
            search_value,
            search_value
        ])

    # បើអ្នកប្រើជ្រើស category បន្ថែមលក្ខខណ្ឌ filter ទៅក្នុង query។
    if selected_category:
        query += " AND category = ?"
        parameters.append(selected_category)

    # រៀប notes តាម id: oldest គឺចាស់មុន, បើមិនដូច្នោះទេថ្មីមុន។
    if sort_order == "oldest":
        query += " ORDER BY id ASC"
    else:
        query += " ORDER BY id DESC"

    # ដំណើរការ query ហើយ fetchall() យក rows ទាំងអស់ជា list។
    notes_list = connection.execute(
        query,
        parameters
    ).fetchall()

    # រាប់ចំនួន notes ទាំងអស់សម្រាប់បង្ហាញនៅលើទំព័រ។
    total_notes = connection.execute(
        "SELECT COUNT(*) AS total FROM notes"
    ).fetchone()["total"]

    # រាប់តែ notes ដែលមាន category ជា Study។
    study_notes = connection.execute(
        "SELECT COUNT(*) AS total FROM notes WHERE category = ?",
        ("Study",)
    ).fetchone()["total"]

    # រាប់តែ notes ដែលមាន category ជា Work។
    work_notes = connection.execute(
        "SELECT COUNT(*) AS total FROM notes WHERE category = ?",
        ("Work",)
    ).fetchone()["total"]

    # បិទ database connection មុនបញ្ជូនទំព័រត្រឡប់។
    connection.close()

    # បញ្ជូន data ទាំងនេះទៅ template notes.html ដើម្បីបង្ហាញ។
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
    # route នេះបង្ហាញទំព័រ About។
    return render_template("about.html")


@app.route("/categories")
def categories():
    # ទាញយក categories ទាំងអស់ពី database។
    category_list = get_all_categories()

    # បញ្ជូន categories ទៅ template categories.html។
    return render_template(
        "categories.html",
        categories=category_list
    )


# route នេះបង្ហាញ form សម្រាប់បង្កើត Category ហើយទទួល form data ពេល submit។
@app.route("/categories/new", methods=["GET", "POST"])
def create_category():
    # POST request កើតឡើងនៅពេលអ្នកប្រើចុចប៊ូតុង Save Category។
    if request.method == "POST":
        # request.form អាន name ពី input ក្នុង form; strip() ដកចន្លោះខាងមុខ និងខាងក្រោយ។
        name = request.form["name"].strip()

        # មិនអនុញ្ញាតឱ្យរក្សាទុក Category ដែលគ្មានឈ្មោះ។
        if not name:
            return render_template(
                "create_category.html",
                error="Category name is required."
            )

        # បើក connection ដើម្បីពិនិត្យ និងរក្សាទុក data ក្នុង database។
        connection = get_db_connection()

        # LOWER() ធ្វើឱ្យ "Study" និង "study" ត្រូវចាត់ទុកថាជាឈ្មោះដូចគ្នា។
        existing_category = connection.execute(
            "SELECT * FROM categories WHERE LOWER(name) = LOWER(?)",
            (name,)
        ).fetchone()

        # បើ Category នេះមានរួចហើយ បិទ connection ហើយបង្ហាញ error។
        if existing_category:
            connection.close()
            return render_template(
                "create_category.html",
                error="This category already exists."
            )

        # INSERT បន្ថែម Category ថ្មី; ? ជា placeholder សម្រាប់ name ដើម្បីធ្វើ SQL query ដោយសុវត្ថិភាព។
        connection.execute(
            "INSERT INTO categories (name) VALUES (?)",
            (name,)
        )

        # commit() រក្សាទុក Category ថ្មី ហើយ connection ត្រូវបានបិទបន្ទាប់មក។
        connection.commit()
        connection.close()

        # flash() បង្ហាញសារ success បន្ទាប់ពី redirect។
        flash("Category created successfully!", "success")

        # url_for() បង្កើត URL ទៅ route categories ហើយ redirect នាំអ្នកប្រើទៅទំព័រនោះ។
        return redirect(url_for("categories"))

    # GET request បង្ហាញ form ទទេ។
    return render_template("create_category.html")


@app.route("/notes/new", methods=["GET", "POST"])
def create_note():
    # ទាញ categories ដើម្បីបង្ហាញក្នុង dropdown របស់ form។
    categories = get_all_categories()

    # GET បង្ហាញ form; POST ទទួល data ដែលអ្នកប្រើ submit ពី form។
    if request.method == "POST":

        # request.form អាន data ពី input fields ក្នុង form ហើយ strip() ដកចន្លោះខាងចុង។
        title = request.form["title"].strip()
        content = request.form["content"].strip()
        category = request.form["category"].strip()

        # ពិនិត្យថា fields ចាំបាច់ទាំងអស់មានតម្លៃ។
        if not title or not content or not category:
            return render_template(
                "create_note.html",
                error="Title, content, and category are required.",
                categories=categories
            )

        # បង្កើតថ្ងៃ និងម៉ោងបច្ចុប្បន្នជាទម្រង់ text សម្រាប់ database។
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        connection = get_db_connection()

        # INSERT បញ្ចូល note ថ្មីទៅក្នុង table notes។
        connection.execute(
            """
            INSERT INTO notes (title, content, category, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (title, content, category, created_at)
        )

        # រក្សាទុក note ថ្មី ហើយបិទ connection។
        connection.commit()
        connection.close()

        # flash បង្កើតសារបណ្តោះអាសន្នសម្រាប់ជូនដំណឹងអ្នកប្រើ។
        flash("Note created successfully!", "success")

        # redirect នាំអ្នកប្រើទៅ route notes ដោយ url_for() បង្កើត URL តាមឈ្មោះ function។
        return redirect(url_for("notes"))

    # សម្រាប់ GET request បង្ហាញ form ទទេ។
    return render_template(
        "create_note.html",
        categories=categories
    )


@app.route("/notes/<int:note_id>")
def view_note(note_id):
    # <int:note_id> ទទួល id ពី URL ហើយបម្លែងវាទៅជា integer។
    note = find_note(note_id)

    # abort(404) បង្ហាញទំព័រ Not Found ប្រសិនបើ note មិនមាន។
    if note is None:
        abort(404)

    # បញ្ជូន note ដែលរកឃើញទៅ template view_note.html។
    return render_template(
        "view_note.html",
        note=note
    )


@app.route("/notes/<int:note_id>/edit", methods=["GET", "POST"])
def edit_note(note_id):
    # ស្វែងរក note ដែលចង់កែសម្រួល។
    note = find_note(note_id)

    # កុំអនុញ្ញាតឱ្យកែ note ដែលមិនមាន។
    if note is None:
        abort(404)

    # ទាញ categories សម្រាប់ dropdown ក្នុង edit form។
    categories = get_all_categories()

    # នៅពេល form ត្រូវបាន submit, ទទួល data ថ្មីពី request.form។
    if request.method == "POST":
        title = request.form["title"].strip()
        content = request.form["content"].strip()
        category = request.form["category"].strip()

        # បើក connection ដើម្បី update note ក្នុង database។
        connection = get_db_connection()

        # UPDATE កែ title, content និង category របស់ note ដែលមាន id ត្រូវគ្នា។
        connection.execute(
            """
            UPDATE notes
            SET title = ?, content = ?, category = ?
            WHERE id = ?
            """,
            (title, content, category, note_id)
        )

        # រក្សាទុកការកែប្រែ ហើយបិទ connection។
        connection.commit()
        connection.close()

        # បង្ហាញសារជោគជ័យបន្ទាប់ពី update។
        flash("Note updated successfully!", "success")

        # នាំអ្នកប្រើទៅទំព័រមើល note ដែលទើបកែ។
        return redirect(url_for("view_note", note_id=note_id))

    # សម្រាប់ GET request បង្ហាញ edit form ដែលមាន data ចាស់របស់ note។
    return render_template(
        "edit_note.html",
        note=note,
        categories=categories
    )


@app.route("/notes/<int:note_id>/delete", methods=["POST"])
def delete_note(note_id):
    # ស្វែងរក note មុនពេលលុប ដើម្បីប្រាកដថាវាមាន។
    note = find_note(note_id)

    # បើគ្មាន note នេះទេ បង្ហាញ 404។
    if note is None:
        abort(404)

    # បើក connection ដើម្បីលុប note ពី database។
    connection = get_db_connection()

    # DELETE លុបតែ row ដែលមាន id ត្រូវនឹង note_id។
    connection.execute(
        "DELETE FROM notes WHERE id = ?",
        (note_id,)
    )

    # រក្សាទុកការលុប ហើយបិទ connection។
    connection.commit()
    connection.close()

    # បង្ហាញសារប្រាប់ថា note ត្រូវបានលុបរួច។
    flash("Note deleted successfully!", "success")

    # នាំអ្នកប្រើត្រឡប់ទៅបញ្ជី notes។
    return redirect(url_for("notes"))


if __name__ == "__main__":
    # Block នេះរត់តែពេលចាប់ផ្ដើម file app.py ដោយផ្ទាល់ប៉ុណ្ណោះ។
    init_db()
    # debug=True បង្ហាញ error លម្អិត និង restart server ពេលកែ code (សម្រាប់ development)។
    app.run(debug=True)
