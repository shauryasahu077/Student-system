from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "student.db")

app = Flask(__name__, template_folder='.')


# Session ke liye secret key
app.secret_key = "student_management_secret_key"


# ---------------- DATABASE HELPERS ----------------

def get_student(enrollment_no, password):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    student = conn.execute(
        """
        SELECT * FROM students
        WHERE enrollment_no = ? AND password = ?
        """,
        (enrollment_no, password)
    ).fetchone()
    conn.close()
    return student


def add_student_db(data):
    conn = sqlite3.connect(DATABASE)
    conn.execute(
        """
        INSERT INTO students
        (enrollment_no, password, name, course, semester, attendance, marks)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["enrollment_no"],
            data["password"],
            data["name"],
            data["course"],
            data["semester"],
            data["attendance"],
            data["marks"]
        )
    )
    conn.commit()
    conn.close()


# ---------------- STUDENT ROUTES ----------------

@app.route("/")
def home():
    if "student_user" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    enrollment_no = request.form["enrollment_no"]
    password = request.form["password"]

    student = get_student(enrollment_no, password)

    if student:
        session["student_user"] = student["enrollment_no"]
        return redirect(url_for("dashboard"))

    return """
    <h2>Invalid Enrollment Number or Password ❌</h2>
    <a href="/">Try Again</a>
    """


@app.route("/dashboard")
def dashboard():
    if "student_user" not in session:
        return redirect(url_for("home"))

    enrollment_no = session["student_user"]
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    student = conn.execute(
        "SELECT * FROM students WHERE enrollment_no = ?",
        (enrollment_no,)
    ).fetchone()
    conn.close()

    return render_template("dashboard.html", student=student)


@app.route("/logout")
def logout():
    session.pop("student_user", None)
    return redirect(url_for("home"))


# ---------------- ADMIN ROUTES ----------------

@app.route("/admin", methods=["GET"])
def admin():
    if "admin_user" in session:
        return redirect(url_for("add_student_route"))
    return render_template("admin_login.html")


@app.route("/admin_login", methods=["POST"])
def admin_login():
    username = request.form["username"]
    password = request.form["password"]

    if username == "admin" and password == "1234":
        session["admin_user"] = username
        return redirect(url_for("add_student_route"))

    return """
    <h2>Invalid Admin Username or Password ❌</h2>
    <br>
    <a href="/admin">Try Again</a>
    """


@app.route("/admin_logout")
def admin_logout():
    session.pop("admin_user", None)
    return redirect(url_for("admin"))


# ---------------- ADD STUDENT ----------------

@app.route("/add_student", methods=["GET", "POST"])
def add_student_route():
    if "admin_user" not in session:
        return redirect(url_for("admin"))

    if request.method == "POST":
        data = {
            "enrollment_no": request.form["enrollment_no"],
            "password": request.form["password"],
            "name": request.form["name"],
            "course": request.form["course"],
            "semester": request.form["semester"],
            "attendance": request.form["attendance"],
            "marks": request.form["marks"]
        }

        try:
            add_student_db(data)
            return redirect(url_for("students"))

        except sqlite3.IntegrityError:
            return """
            <h2>Enrollment Number Already Exists ❌</h2>
            <br>
            <a href="/add_student">Go Back</a>
            """

    return render_template("admin.html")


# ---------------- ALL STUDENTS + SEARCH ----------------

@app.route("/students")
def students():
    if "admin_user" not in session:
        return redirect(url_for("admin"))

    search = request.args.get("search", "").strip()

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    if search:
        students = conn.execute(
            """
            SELECT * FROM students
            WHERE enrollment_no LIKE ?
            OR name LIKE ?
            """,
            ("%" + search + "%", "%" + search + "%")
        ).fetchall()
    else:
        students = conn.execute("SELECT * FROM students").fetchall()

    conn.close()

    return render_template("students.html", students=students, search=search)


# ---------------- EDIT STUDENT ----------------

@app.route("/edit/<enrollment_no>")
def edit_student(enrollment_no):
    if "admin_user" not in session:
        return redirect(url_for("admin"))

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    student = conn.execute(
        "SELECT * FROM students WHERE enrollment_no = ?",
        (enrollment_no,)
    ).fetchone()

    conn.close()

    if student:
        return render_template("edit_student.html", student=student)

    return """
    <h2>Student Not Found ❌</h2>
    <br>
    <a href="/students">Back to Students</a>
    """


# ---------------- UPDATE STUDENT ----------------

@app.route("/update/<enrollment_no>", methods=["POST"])
def update_student(enrollment_no):
    if "admin_user" not in session:
        return redirect(url_for("admin"))

    password = request.form["password"]
    name = request.form["name"]
    course = request.form["course"]
    semester = request.form["semester"]
    attendance = request.form["attendance"]
    marks = request.form["marks"]

    conn = sqlite3.connect(DATABASE)
    conn.execute(
        """
        UPDATE students
        SET password = ?,
            name = ?,
            course = ?,
            semester = ?,
            attendance = ?,
            marks = ?
        WHERE enrollment_no = ?
        """,
        (password, name, course, semester, attendance, marks, enrollment_no)
    )
    conn.commit()
    conn.close()

    return redirect(url_for("students"))


# ---------------- DELETE STUDENT ----------------

@app.route("/delete/<enrollment_no>")
def delete_student(enrollment_no):
    if "admin_user" not in session:
        return redirect(url_for("admin"))

    conn = sqlite3.connect(DATABASE)
    conn.execute(
        "DELETE FROM students WHERE enrollment_no = ?",
        (enrollment_no,)
    )
    conn.commit()
    conn.close()

    return redirect(url_for("students"))


# ---------------- START SERVER ----------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
