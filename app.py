from flask import Flask, render_template, request, redirect, url_for, flash, session
from database import get_db_connection, create_tables
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask import send_file
from reportlab.pdfgen import canvas
import io
app = Flask(__name__)
app.secret_key = "student_tracker_secret"

DATABASE = "database.db"


# ==========================
# DATABASE CONNECTION
# ==========================

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ==========================
# CREATE TABLES
# ==========================

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    # USERS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
    """)

    # STUDENTS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT NOT NULL,
        rollno TEXT UNIQUE NOT NULL,
        gender TEXT NOT NULL
    )
    """)

    # GRADES TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS grades(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT NOT NULL,
        rollno TEXT NOT NULL,

        telugu INTEGER,
        hindi INTEGER,
        english INTEGER,
        social INTEGER,
        physics INTEGER,
        maths INTEGER,
        biology INTEGER
    )
    """)

    conn.commit()
    conn.close()


create_tables()


# ==========================
# LANDING PAGE
# ==========================

@app.route("/")
def home():
    return render_template("title_page.html")


# ==========================
# SIGNUP
# ==========================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        fullname = request.form["fullname"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        role = request.form["role"]

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("signup"))

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()

        try:
            conn.execute("""
            INSERT INTO users(fullname,email,password,role)
            VALUES(?,?,?,?)
            """, (
                fullname,
                email,
                hashed_password,
                role
            ))

            conn.commit()

            flash("Account Created Successfully!", "success")
            return redirect(url_for("signin"))

        except sqlite3.IntegrityError:
            flash("Email already exists!", "danger")

        finally:
            conn.close()

    return render_template("signup.html")


# ==========================
# SIGNIN
# ==========================

@app.route("/signin", methods=["GET", "POST"])
def signin():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()

        user = conn.execute("""
        SELECT * FROM users
        WHERE email=?
        """, (email,)).fetchone()

        conn.close()

        if user:

            if check_password_hash(
                user["password"],
                password
            ):

                session["user_id"] = user["id"]
                session["fullname"] = user["fullname"]
                session["email"] = user["email"]   # <-- Add this line
                session["role"] = user["role"]
                session["email"] = user["email"]
                flash("Login Successful!", "success")
                return redirect(url_for("dashboard"))

        flash("Invalid Email or Password!", "danger")

    return render_template("signin.html")
# ==========================
# DASHBOARD
# ==========================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("signin"))

    conn = get_db_connection()

    # Logged in user details
    user = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (session["user_id"],)).fetchone()

    total_students = conn.execute("""
        SELECT COUNT(*) as total
        FROM students
    """).fetchone()["total"]

    grades = conn.execute("""
        SELECT *
        FROM grades
    """).fetchall()

    pass_students = 0
    fail_students = 0
    total_percentage = 0

    for row in grades:

        marks = [
            row["telugu"],
            row["hindi"],
            row["english"],
            row["social"],
            row["physics"],
            row["maths"],
            row["biology"]
        ]

        total = sum(marks)
        percentage = total / 7
        total_percentage += percentage

        if min(marks) < 35:
            fail_students += 1
        else:
            pass_students += 1

    average_percentage = 0

    if len(grades) > 0:
        average_percentage = round(
            total_percentage / len(grades), 2
        )

    conn.close()

    return render_template(
        "dashboard.html",
        total_students=total_students,
        pass_students=pass_students,
        fail_students=fail_students,
        average_percentage=average_percentage,
        user=user          # <-- Idi compulsory
    )
# ==========================
# ADD STUDENT
# ==========================

@app.route("/add_student", methods=["GET", "POST"])
def add_student():

    if "user_id" not in session:
        return redirect(url_for("signin"))

    conn = get_db_connection()

    if request.method == "POST":

        fullname = request.form["fullname"]
        rollno = request.form["rollno"]
        gender = request.form["gender"]

        try:

            conn.execute("""
                INSERT INTO students(fullname, rollno, gender)
                VALUES (?, ?, ?)
            """, (fullname, rollno, gender))

            conn.commit()

            flash("Student Added Successfully!", "success")

        except sqlite3.IntegrityError:

            flash("Roll Number Already Exists!", "danger")

    # IMPORTANT PART
    students = conn.execute(
        "SELECT * FROM students"
    ).fetchall()

    conn.close()

    return render_template(
        "add_student.html",
        students=students
    )
@app.route("/delete_add_student/<int:id>")
def delete_add_student(id):

    if "user_id" not in session:
        return redirect(url_for("signin"))

    conn = get_db_connection()

    student = conn.execute(
        "SELECT rollno FROM students WHERE id = ?",
        (id,)
    ).fetchone()

    if student:

        rollno = student["rollno"]

        # grades table nundi delete
        conn.execute(
            "DELETE FROM grades WHERE rollno = ?",
            (rollno,)
        )

        # students table nundi delete
        conn.execute(
            "DELETE FROM students WHERE id = ?",
            (id,)
        )

        conn.commit()

    conn.close()

    flash("Student deleted successfully!", "success")

    return redirect(url_for("add_student"))

# ==========================
# ADD GRADES
# ==========================

@app.route("/add_grades", methods=["GET", "POST"])
def add_grades():

    if "user_id" not in session:
        return redirect(url_for("signin"))

    if request.method == "POST":

        student_name = request.form["student_name"]
        rollno = request.form["rollno"]

        telugu = int(request.form["telugu"])
        hindi = int(request.form["hindi"])
        english = int(request.form["english"])
        social = int(request.form["social"])
        physics = int(request.form["physics"])
        maths = int(request.form["maths"])
        biology = int(request.form["biology"])

        conn = get_db_connection()

        conn.execute("""
        INSERT INTO grades(
            student_name,
            rollno,
            telugu,
            hindi,
            english,
            social,
            physics,
            maths,
            biology
        )
        VALUES(?,?,?,?,?,?,?,?,?)
        """,
        (
            student_name,
            rollno,
            telugu,
            hindi,
            english,
            social,
            physics,
            maths,
            biology
        ))

        conn.commit()
        conn.close()

        flash("Grades Added Successfully!", "success")

    return render_template("add_grades.html")


# ==========================
# REPORT CARD
# ==========================

@app.route("/report_card")
def report_card():

    if "user_id" not in session:
        return redirect(url_for("signin"))

    conn = get_db_connection()

    report = conn.execute("""
    SELECT *
    FROM grades
    ORDER BY id DESC
    LIMIT 1
    """).fetchone()

    conn.close()

    if not report:
        flash("No Report Available!", "warning")
        return redirect(url_for("dashboard"))

    marks = [
        report["telugu"] or 0,
        report["hindi"] or 0,
        report["english"] or 0,
        report["social"] or 0,
        report["physics"] or 0,
        report["maths"] or 0,
        report["biology"] or 0
    ]

    total_marks = sum(marks)
    average = round(total_marks / 7, 2)
    percentage = round((total_marks / 700) * 100, 2)

    if percentage >= 90:
        grade = "A+"
    elif percentage >= 80:
        grade = "A"
    elif percentage >= 70:
        grade = "B"
    elif percentage >= 60:
        grade = "C"
    elif percentage >= 50:
        grade = "D"
    else:
        grade = "F"

    status = "Fail" if min(marks) < 35 else "Pass"

    return render_template(
        "report_card.html",
        report=report,
        total_marks=total_marks,
        average=average,
        percentage=percentage,
        grade=grade,
        status=status
    )
@app.route("/download_report")
def download_report():

    if "user_id" not in session:
        return redirect(url_for("signin"))

    conn = get_db_connection()

    report = conn.execute("""
    SELECT *
    FROM grades
    ORDER BY id DESC
    LIMIT 1
    """).fetchone()

    conn.close()

    if not report:
        return "No Report Found"

    marks = [
        report["telugu"] or 0,
        report["hindi"] or 0,
        report["english"] or 0,
        report["social"] or 0,
        report["physics"] or 0,
        report["maths"] or 0,
        report["biology"] or 0
    ]

    total_marks = sum(marks)
    percentage = round((total_marks / 700) * 100, 2)

    buffer = io.BytesIO()

    pdf = canvas.Canvas(buffer)

    pdf.setTitle("Student Report Card")

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(180, 800, "STUDENT REPORT CARD")

    pdf.setFont("Helvetica", 12)

    pdf.drawString(50, 760, f"Name : {report['student_name']}")
    pdf.drawString(50, 740, f"Roll No : {report['rollno']}")

    pdf.drawString(50, 700, f"Telugu : {report['telugu']}")
    pdf.drawString(50, 680, f"Hindi : {report['hindi']}")
    pdf.drawString(50, 660, f"English : {report['english']}")
    pdf.drawString(50, 640, f"Social : {report['social']}")
    pdf.drawString(50, 620, f"Physics : {report['physics']}")
    pdf.drawString(50, 600, f"Maths : {report['maths']}")
    pdf.drawString(50, 580, f"Biology : {report['biology']}")

    pdf.drawString(50, 520, f"Total Marks : {total_marks}/700")
    pdf.drawString(50, 500, f"Percentage : {percentage}%")

    pdf.save()

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"{report['student_name']}_ReportCard.pdf",
        mimetype="application/pdf"
    )

# ==========================
# STUDENT HISTORY
# ==========================

@app.route("/history")
def history():

    if "user_id" not in session:
        return redirect(url_for("signin"))

    conn = get_db_connection()

    records = conn.execute("""
    SELECT *
    FROM grades
    """).fetchall()

    history_data = []

    for row in records:

        marks = [
            row["telugu"],
            row["hindi"],
            row["english"],
            row["social"],
            row["physics"],
            row["maths"],
            row["biology"]
        ]

        status = "Pass"

        if min(marks) < 35:
            status = "Fail"

        history_data.append({
           "id": row["id"],
           "name": row["student_name"],
           "rollno": row["rollno"],
           "status": status
})
    conn.close()

    return render_template(
        "history.html",
        students=history_data
    )
@app.route("/delete_student/<int:id>")
def delete_student(id):

    if "user_id" not in session:
        return redirect(url_for("signin"))

    conn = get_db_connection()

    # First get roll number from grades table
    student = conn.execute(
        "SELECT rollno FROM grades WHERE id = ?",
        (id,)
    ).fetchone()

    if student:

        rollno = student["rollno"]

        # Delete from grades table using rollno
        conn.execute(
            "DELETE FROM grades WHERE rollno = ?",
            (rollno,)
        )

        # Delete from students table using rollno
        conn.execute(
            "DELETE FROM students WHERE rollno = ?",
            (rollno,)
        )

        conn.commit()

    conn.close()

     #flash("Student deleted successfully!", "success")

    return redirect(url_for("history"))

# ==========================
# LOGOUT
# ==========================

@app.route("/logout")
def logout():

    session.clear()

    flash("Logged Out Successfully!", "success")

    return redirect(url_for("signin"))
@app.route("/study_suggestions")
def study_suggestions():

    if "user_id" not in session:
        return redirect(url_for("signin"))

    conn = get_db_connection()

    report = conn.execute("""
    SELECT *
    FROM grades
    ORDER BY id DESC
    LIMIT 1
    """).fetchone()

    conn.close()

    if not report:
        flash("No Report Available!", "warning")
        return redirect(url_for("dashboard"))

    marks = {
        "Telugu": report["telugu"],
        "Hindi": report["hindi"],
        "English": report["english"],
        "Social": report["social"],
        "Physics": report["physics"],
        "Maths": report["maths"],
        "Biology": report["biology"]
    }

    total_marks = sum(marks.values())
    percentage = round((total_marks / 700) * 100, 2)

    student_name = report["student_name"]

    # Overall performance message
    if percentage >= 90:
        performance = "Excellent"
        overall_message = (
            f"🎉 Dear {student_name}, Excellent performance! "
            "Keep up the great work."
        )

    elif percentage >= 75:
        performance = "Very Good"
        overall_message = (
            f"👏 Dear {student_name}, Very good performance. "
            "You can score even higher with regular revision."
        )

    elif percentage >= 50:
        performance = "Average"
        overall_message = (
            f"🙂 Dear {student_name}, Your performance is average. "
            "Focus more on weak subjects."
        )

    else:
        performance = "Poor"
        overall_message = (
            f"⚠️ Dear {student_name}, Your performance needs improvement. "
            "Do not lose confidence and practice daily."
        )

    # Weak subjects
    weak_subjects = []
    suggestions = []

    for subject, mark in marks.items():

        if mark < 35:

            weak_subjects.append(f"{subject} ({mark} Marks)")

            if subject == "Maths":
                suggestions.append(
                    "➕ Practice Maths problems and formulas daily."
                )

            elif subject == "English":
                suggestions.append(
                    "📖 Improve vocabulary and reading skills."
                )

            elif subject == "Physics":
                suggestions.append(
                    "🔬 Focus on concepts and numerical problems."
                )

            elif subject == "Biology":
                suggestions.append(
                    "🧬 Revise diagrams and important definitions."
                )

            elif subject == "Social":
                suggestions.append(
                    "🌍 Read chapters regularly and make short notes."
                )

            elif subject == "Telugu":
                suggestions.append(
                    "📝 Practice writing and grammar exercises."
                )

            elif subject == "Hindi":
                suggestions.append(
                    "📚 Improve grammar and reading practice."
                )

    return render_template(
        "study_suggestions.html",
        student_name=student_name,
        percentage=percentage,
        performance=performance,
        overall_message=overall_message,
        weak_subjects=weak_subjects,
        suggestions=suggestions
    )
@app.route("/total_students_list")
def total_students_list():

    conn = get_db_connection()

    students = conn.execute("""
        SELECT fullname, rollno
        FROM students
    """).fetchall()

    conn.close()

    return render_template(
        "total_students.html",
        students=students
    )
@app.route("/pass_students_list")
def pass_students_list():

    if "user_id" not in session:
        return redirect(url_for("signin"))

    conn = get_db_connection()

    students = conn.execute("""
        SELECT
            student_name,
            rollno,

            (telugu + hindi + english +
             social + physics + maths +
             biology) AS total_marks

        FROM grades

        WHERE
            (telugu + hindi + english +
             social + physics + maths +
             biology) >= 245
    """).fetchall()

    conn.close()

    return render_template(
        "pass_students.html",
        students=students
    )
@app.route("/fail_students_list")
def fail_students_list():

    if "user_id" not in session:
        return redirect(url_for("signin"))

    conn = get_db_connection()

    students = conn.execute("""
        SELECT *
        FROM grades
    """).fetchall()

    conn.close()

    fail_students = []

    for student in students:

        failed_subjects = []

        if student["telugu"] < 35:
            failed_subjects.append("Telugu")

        if student["hindi"] < 35:
            failed_subjects.append("Hindi")

        if student["english"] < 35:
            failed_subjects.append("English")

        if student["social"] < 35:
            failed_subjects.append("Social")

        if student["physics"] < 35:
            failed_subjects.append("Physics")

        if student["maths"] < 35:
            failed_subjects.append("Maths")

        if student["biology"] < 35:
            failed_subjects.append("Biology")

        # Student fail ayithe list lo add cheyyi
        if failed_subjects:

            fail_students.append({
                "student_name": student["student_name"],
                "rollno": student["rollno"],
                "failed_subjects": ", ".join(failed_subjects)
            })

    return render_template(
        "fail_students.html",
        students=fail_students
    )   
@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']

        conn = get_db_connection()
        conn.execute(
            "UPDATE users SET fullname=?, email=? WHERE id=?",
            (fullname, email, session['user_id'])
        )
        conn.commit()
        conn.close()

        session['fullname'] = fullname
        session['email'] = email

        return redirect(url_for('dashboard'))

    return render_template('edit_profile.html')


@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        new_password = request.form['new_password']

        conn = get_db_connection()
        conn.execute(
            "UPDATE users SET password=? WHERE id=?",
            (new_password, session['user_id'])
        )
        conn.commit()
        conn.close()

        return redirect(url_for('dashboard'))

    return render_template('change_password.html') 
@app.route('/subject_topper', methods=['GET', 'POST'])
def subject_topper():

    topper = None

    if request.method == 'POST':

        subject = request.form['subject']

        conn = get_db_connection()
        cursor = conn.cursor()

        query = f"""
            SELECT student_name, rollno, {subject}
            FROM grades
            ORDER BY {subject} DESC
            LIMIT 1
        """

        cursor.execute(query)
        topper = cursor.fetchone()

        conn.close()

    return render_template(
        'subject_topper.html',
        topper=topper
    )
@app.route('/class_average', methods=['GET', 'POST'])
def class_average():

    average = None

    if request.method == 'POST':

        subject = request.form['subject']

        conn = get_db_connection()
        cursor = conn.cursor()

        query = f"""
            SELECT AVG({subject}) as avg_marks
            FROM grades
        """

        cursor.execute(query)

        result = cursor.fetchone()

        average = round(result['avg_marks'], 2)

        conn.close()

    return render_template(
        'class_average.html',
        average=average
    )
# ==========================
# RUN APP
# ==========================

if __name__ == "__main__":
    app.run(debug=True)