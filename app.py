from flask import Flask, request, session, url_for, redirect, render_template
import mysql.connector
from mysql.connector import pooling
import re 
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db_pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
    port=int(os.getenv("DB_PORT", 3306))
)

def get_db():
    return db_pool.get_connection()

app.secret_key = os.getenv("SECRET_KEY")


@app.route("/", methods=["GET", "POST"])
def homepage():
    return render_template("login.html")


@app.route("/student", methods=["GET", "POST"])
def student():
    msg = ""

    if request.method == "POST":
        roll_no = request.form.get("roll_no")
        password = request.form.get("password")

        if roll_no and password:
            conn = get_db()
            cursor = conn.cursor(dictionary=True, buffered=True)

            sql = "SELECT * FROM students WHERE roll_no=%s AND password=%s"
            cursor.execute(sql, (roll_no, password,))
            students = cursor.fetchone()

            cursor.close()
            conn.close()

            if students:
                session["logginid"] = students["id"]
                session["roll_no"] = students["roll_no"]
                session["password"] = students["password"]
                return redirect(url_for("student_dashboard"))
            else:
                msg = "Incorrect roll no or password"
        else:
            msg = "Put both roll no and password"

    return render_template("student.html", msg=msg)


@app.route("/registration_student", methods=["GET", "POST"])
def registration_student():
    msg = ""

    if request.method == "POST":
        roll_no = request.form.get("roll_no")
        password = request.form.get("password")

        if roll_no and password:
            conn = get_db()
            cursor = conn.cursor(dictionary=True, buffered=True)

            sql = "SELECT * FROM students WHERE roll_no=%s AND password=%s"
            cursor.execute(sql, (roll_no, password,))
            students = cursor.fetchone()

            if students:
                msg = "You already have an account"
            else:
                sql = "INSERT INTO students(roll_no, password) VALUES(%s, %s)"
                cursor.execute(sql, (roll_no, password,))
                conn.commit()
                msg = "You have successfully registered"

            cursor.close()
            conn.close()
        else:
            msg = "Fill both roll no and password"

    return render_template("student_registration.html", msg=msg)


@app.route("/student_dashboard", methods=["GET", "POST"])
def student_dashboard():
    conn = get_db()
    cursor = conn.cursor(dictionary=True, buffered=True)

    cursor.execute(
        "SELECT roll_no, IFNULL(photo,'default.png') AS photo FROM students WHERE roll_no=%s",
        (session["roll_no"],)
    )
    student = cursor.fetchone()

    cursor.execute(
        "SELECT name, roll_no FROM students WHERE roll_no=%s",
        (session["roll_no"],)
    )
    student1 = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template("student_dashboard.html", student=student, student1=student1)


@app.route("/student_profile_edit", methods=["GET", "POST"])
def student_profile_edit():
    conn = get_db()
    cursor = conn.cursor(dictionary=True, buffered=True)

    if request.method == "POST":
        file = request.files.get("photo")

        if file and file.filename != "":
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            cursor.execute(
                "UPDATE students SET photo=%s WHERE roll_no=%s",
                (filename, session["roll_no"])
            )
            conn.commit()

        name = request.form.get("name")
        roll_no = request.form.get("roll_no")

        if name and roll_no:
            cursor.execute(
                "UPDATE students SET name=%s WHERE roll_no=%s",
                (name, roll_no,)
            )
            conn.commit()
            session["roll_no"] = roll_no

    cursor.execute(
        "SELECT roll_no, photo FROM students WHERE roll_no=%s",
        (session["roll_no"],)
    )
    student = cursor.fetchone()

    cursor.execute(
        "SELECT * FROM students WHERE roll_no=%s",
        (session["roll_no"],)
    )
    student1 = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template("student_profile_edit.html", student=student, student1=student1)


@app.route('/student_subjects')
def student_subjects():
    if 'logginid' not in session:
        return redirect('/')

    conn = get_db()
    cursor = conn.cursor(dictionary=True, buffered=True)

    cursor.execute(
        "SELECT selected_subjects FROM students WHERE id=%s",
        (session['logginid'],)
    )
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    selected_subjects = []
    if result and result['selected_subjects']:
        selected_subjects = result['selected_subjects'].split(',')

    return render_template("student_subjects.html", selected_subjects=selected_subjects)


@app.route('/save_subjects', methods=['POST'])
def save_subjects():
    if 'logginid' not in session:
        return redirect('/')

    subjects = request.form.getlist('subjects')

    if len(subjects) != 3:
        return "Please select exactly 3 subjects"

    selected = ",".join(subjects)

    conn = get_db()
    cursor = conn.cursor(dictionary=True, buffered=True)

    cursor.execute(
        "UPDATE students SET selected_subjects=%s WHERE id=%s",
        (selected, session['logginid'])
    )
    conn.commit()

    cursor.close()
    conn.close()

    return redirect('/student_subjects')


@app.route("/student_marks", methods=["GET", "POST"])
def student_marks():
    if 'logginid' not in session:
        return redirect('/')

    conn = get_db()
    cursor = conn.cursor(dictionary=True, buffered=True)

    cursor.execute(
        "SELECT selected_subjects FROM students WHERE id=%s",
        (session['logginid'],)
    )
    result = cursor.fetchone()

    subjects = []
    if result and result['selected_subjects']:
        subjects = result['selected_subjects'].split(",")

    cursor.execute(
        "SELECT subject, marks FROM marks WHERE student_id=%s",
        (session['logginid'],)
    )
    marks_data = cursor.fetchall()

    cursor.close()
    conn.close()

    marks_dict = {}
    for row in marks_data:
        marks_dict[row["subject"]] = row["marks"]

    return render_template("student_marks.html", subjects=subjects, marks_dict=marks_dict)


@app.route("/teacher", methods=["GET", "POST"])
def teacher():
    msg = ""

    if request.method == "POST":
        id_no = request.form.get("id_no")
        password = request.form.get("password")

        if id_no and password:
            conn = get_db()
            cursor = conn.cursor(dictionary=True, buffered=True)

            sql = "SELECT * FROM teachers WHERE id_no=%s AND password=%s"
            cursor.execute(sql, (id_no, password,))
            teachers = cursor.fetchone()

            cursor.close()
            conn.close()

            if teachers:
                session["logginid"] = teachers["id"]
                session["password"] = teachers["password"]
                return redirect(url_for("teacher_dashboard"))
            else:
                msg = "Incorrect id no or password"
        else:
            msg = "Put both id no and password"

    return render_template("teacher.html", msg=msg)


@app.route("/registration_teacher", methods=["GET", "POST"])
def registration_teacher():
    msg = ""

    if request.method == "POST":
        id_no = request.form.get("id_no")
        password = request.form.get("password")

        if id_no and password:
            conn = get_db()
            cursor = conn.cursor(dictionary=True, buffered=True)

            sql = "SELECT * FROM teachers WHERE id_no=%s AND password=%s"
            cursor.execute(sql, (id_no, password,))
            teachers = cursor.fetchone()

            if teachers:
                msg = "You already have an account"
            else:
                sql = "INSERT INTO teachers(id_no, password) VALUES(%s, %s)"
                cursor.execute(sql, (id_no, password,))
                conn.commit()
                msg = "You have successfully registered"

            cursor.close()
            conn.close()
        else:
            msg = "Fill both id no and password"

    return render_template("teacher_registration.html", msg=msg)


@app.route("/teacher_dashboard", methods=["GET", "POST"])
def teacher_dashboard():
    conn = get_db()
    cursor = conn.cursor(dictionary=True, buffered=True)

    if request.method == 'POST':
        student_id = request.form.get("student_id")

        subjects = [
            request.form.get("subject1"),
            request.form.get("subject2"),
            request.form.get("subject3")
        ]

        marks = [
            request.form.get("marks1"),
            request.form.get("marks2"),
            request.form.get("marks3")
        ]

        for subject, mark in zip(subjects, marks):
            cursor.execute(
                "SELECT * FROM marks WHERE student_id=%s AND subject=%s",
                (student_id, subject)
            )
            existing = cursor.fetchone()

            if existing:
                cursor.execute(
                    "UPDATE marks SET marks=%s WHERE student_id=%s AND subject=%s",
                    (mark, student_id, subject)
                )
            else:
                cursor.execute(
                    "INSERT INTO marks(student_id, subject, marks) VALUES(%s, %s, %s)",
                    (student_id, subject, mark)
                )

        conn.commit()

    cursor.execute("""
        SELECT id, name, roll_no,
        IFNULL(selected_subjects,'') AS selected_subjects
        FROM students
        WHERE selected_subjects IS NOT NULL
    """)
    students = cursor.fetchall()

    cursor.execute("SELECT student_id, subject, marks FROM marks")
    marks_data = cursor.fetchall()

    cursor.close()
    conn.close()

    marks_dict = {}
    for row in marks_data:
        marks_dict[(row["student_id"], row["subject"])] = row["marks"]

    return render_template(
        "teacher_dashboard.html",
        students=students,
        marks_dict=marks_dict
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))


# from flask import Flask, request, session, url_for, redirect, render_template
# import mysql.connector
# import re 
# import os
# from werkzeug.utils import secure_filename
# # from werkzeug.security import generate_password_hash, check_password_hash
# from dotenv import load_dotenv
# load_dotenv()

# app = Flask(__name__)
# # app.secret_key = "secretkey"

# UPLOAD_FOLDER = 'static/uploads'
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# # student_data = {
# #     "name": "Nitam Biswas",
# #     "roll": "12345",
# #     "image": "default.png"
# # }

# # db = mysql.connector.connect(
# #    host="localhost",
# #    user="root",
# #    password="121997",
# #    database="university_portal1" 
# # )

# # db = mysql.connector.connect(
# #    host=os.getenv("DB_HOST"),
# #    user=os.getenv("DB_USER"),
# #    password=os.getenv("DB_PASSWORD"),
# #    database=os.getenv("DB_NAME")
# # )

# try:
#     db = mysql.connector.connect(
#         host=os.getenv("DB_HOST"),
#         user=os.getenv("DB_USER"),
#         password=os.getenv("DB_PASSWORD"),
#         database=os.getenv("DB_NAME"),
#         port=int(os.getenv("DB_PORT", 3306))
#     )
#     cursor = db.cursor(dictionary=True, buffered=True)
#     print("Database connected successfully!")
# except Exception as e:
#     print(f"Database connection failed: {e}")

# app.secret_key = os.getenv("SECRET_KEY")

# # cursor = db.cursor(dictionary=True)

# @app.route("/", methods=["GET", "POST"])
# def homepage():
#      return render_template("login.html")

# @app.route("/student", methods=["GET", "POST"])
# def student():
#    msg = ""

#    if request.method == "POST":
#       roll_no = request.form.get("roll_no")
#       password = request.form.get("password")

#       if roll_no and password:
#          cursor = db.cursor(dictionary=True, buffered=True)

#          sql = "select * from students where roll_no =%s and password=%s"
#          cursor.execute(sql,(roll_no, password,))
#          students = cursor.fetchone()

#          if students:
#             session["logginid"] = students["id"]
#             session["roll_no"] = students["roll_no"]
#             session["password"] = students["password"]
#             cursor.close()
#             db.commit()
#             return redirect (url_for("student_dashboard"))
#          else:
#             msg = "Incorrect roll no or password"
#       else:
#        msg = "Put both roll no and password"
   
#    return render_template("student.html", msg=msg)


# @app.route("/registration_student", methods=["GET", "POST"])
# def registration_student():
#    msg = ""

#    if request.method == "POST":
#       roll_no = request.form.get("roll_no")
#       password = request.form.get("password")
#       # hashed_password = generate_password_hash(password)

#       if roll_no and password:
#          cursor = db.cursor(dictionary=True, buffered=True)

#          sql = "select * from students where roll_no = %s and password = %s"
#          cursor.execute(sql, (roll_no, password,))
#          students = cursor.fetchone()

#          if students:
#             msg = "You already have an account"
#          else:
#             sql = "insert into students(roll_no, password) values(%s, %s)"
#             cursor.execute(sql, (roll_no, password,))
#             cursor.close()
#             db.commit()
#             msg = "You have successfully registered"
#       else:
#          msg = "Fill both roll no and password"
#    return render_template("student_registration.html", msg=msg)

# @app.route("/student_dashboard", methods=["GET", "POST"])
# def student_dashboard():
#    # return render_template("student_dashboard.html")
#    # return render_template("student_dashboard.html", student=student_data)
#    # cursor.execute(
#    #      "SELECT roll_no, photo FROM students WHERE roll_no=%s",
#    #      (session["roll_no"],)
#    #  )

#    cursor.execute("SELECT roll_no, IFNULL(photo,'default.png') AS photo FROM students WHERE roll_no=%s",(session["roll_no"],))  
#    student = cursor.fetchone()

#    cursor.execute("select name, roll_no from students where roll_no=%s", (session["roll_no"],))
#    student1 = cursor.fetchone()

#    return render_template("student_dashboard.html", student=student, student1=student1)
   
# @app.route("/student_profile_edit", methods=["GET", "POST"])
# def student_profile_edit():
#    # return render_template("student_profile_edit.html")
#    # if request.method == "POST":

#    #      file = request.files['photo']

#    #      if file.filename != "":
#    #          filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
#    #          file.save(filepath)

#    #          student_data["image"] = file.filename

#    #      return redirect(url_for('student_dashboard'))

#    # return render_template("student_profile_edit.html", student=student_data)
#    cursor = db.cursor(dictionary=True, buffered=True)
#    # student1 = None

#    if request.method == "POST":
#     file = request.files.get("photo")

#     if file and file.filename != "":
#      filename = secure_filename(file.filename)
#      filepath = os.path.join(app.config["UPLOAD_FOLDER"],filename)
#      file.save(filepath)

#      cursor.execute("UPDATE students SET photo=%s WHERE roll_no=%s",(filename, session["roll_no"]))
#      db.commit()
     
#    #   return redirect(url_for("student_dashboard"))

#    cursor.execute("SELECT roll_no, photo FROM students WHERE roll_no=%s",(session["roll_no"],))
#    student = cursor.fetchone()

#    if request.method == "POST":
#       name = request.form.get("name")
#       roll_no = request.form.get("roll_no")

#       if name and roll_no:
#          cursor = db.cursor(dictionary=True, buffered=True)

#          sql ="UPDATE students SET name=%s WHERE roll_no=%s"
#          cursor.execute(sql, (name, roll_no,))
#          db.commit()

#          session["roll_no"] = roll_no

#    cursor.execute("SELECT * FROM students WHERE roll_no=%s", (session["roll_no"],))
#    student1 = cursor.fetchone()
#    cursor.close()

#    return render_template("student_profile_edit.html", student=student, student1=student1 )

# @app.route('/student_subjects')
# def student_subjects():
#    #  return render_template('student_subjects.html')

#    if 'logginid' not in session:
#       return redirect('/')

#    query = """SELECT selected_subjects FROM students WHERE id = %s"""

#    cursor.execute(query, (session['logginid'],))
#    result = cursor.fetchone()

#    selected_subjects = []

#    if result and result['selected_subjects']:
#       selected_subjects = result['selected_subjects'].split(',')

#    # clear_checkbox = session.pop('clear_checkbox', False)

#    # if clear_checkbox:
#    #    selected_subjects = []

#    # clear_checkbox = session.pop('clear_checkbox', False)

#    # checkbox_subjects = [] if clear_checkbox else selected_subjects


#    return render_template(
#         "student_subjects.html",
#         selected_subjects=selected_subjects,
#     )
   
# @app.route('/save_subjects', methods=['POST'])
# def save_subjects():

#     if 'logginid' not in session:
#         return redirect('/')

#     subjects = request.form.getlist('subjects')

#     if len(subjects) != 3:
#         return "Please select exactly 3 subjects"

#     selected = ",".join(subjects)

#     update_query = """
#     UPDATE students
#     SET selected_subjects = %s
#     WHERE id = %s
#     """

#     cursor.execute(update_query, (selected, session['logginid']))
#     db.commit()
     
#    #  session['clear_checkbox'] = True

#     return redirect('/student_subjects')

# @app.route("/student_marks", methods=["GET", "POST"])
# def student_marks():
#    # if 'logginid' not in session:
#    #      return redirect('/')

#    # cursor.execute(
#    #      "SELECT selected_subjects FROM students WHERE id=%s",
#    #      (session['logginid'],)
#    #  )

#    # result = cursor.fetchone()

#    # subjects = []

#    # if result and result['selected_subjects']:
#    #      subjects = result['selected_subjects'].split(',')

#    # return render_template(
#    #      "student_marks.html",
#    #      subjects=subjects
#    #  )

#    if 'logginid' not in session:
#         return redirect('/')

#    cursor = db.cursor(dictionary=True, buffered=True)

#     # get student's selected subjects
#    cursor.execute(
#         "SELECT selected_subjects FROM students WHERE id=%s",
#         (session['logginid'],)
#     )

#    result = cursor.fetchone()

#    subjects = []

#    if result and result['selected_subjects']:
#         subjects = result['selected_subjects'].split(",")

#     # get marks entered by teacher
#    cursor.execute(
#         """
#         SELECT subject, marks
#         FROM marks
#         WHERE student_id=%s
#         """,
#         (session['logginid'],)
#     )

#    marks_data = cursor.fetchall()

#    marks_dict = {}

#    for row in marks_data:
#       marks_dict[row["subject"]] = row["marks"]

#    return render_template(
#         "student_marks.html",
#         subjects=subjects,
#         marks_dict=marks_dict
#     )

# @app.route("/teacher", methods=["GET", "POST"])
# def teacher():
#    msg = ""

#    if request.method == "POST":
#       id_no = request.form.get("id_no")
#       password = request.form.get("password")

#       if id_no and password:
#          cursor = db.cursor(dictionary=True, buffered=True)

#          sql = "select * from teachers where id_no =%s and password=%s"
#          cursor.execute(sql,(id_no, password,))
#          teachers = cursor.fetchone()

#          if teachers:
#             session["logginid"] = teachers["id"]
#             session["password"] = teachers["password"]
#             cursor.close()
#             db.commit()
#             return redirect (url_for("teacher_dashboard"))
#          else:
#             msg = "Incorrect id no or password"
#       else:
#        msg = "Put both id no and password"
   
#    return render_template("teacher.html", msg=msg)
  

# @app.route("/registration_teacher", methods=["GET", "POST"])
# def registration_teacher():
#    msg = ""

#    if request.method == "POST":
#       id_no = request.form.get("id_no")
#       password = request.form.get("password")

#       if id_no and password:
#          cursor = db.cursor(dictionary=True, buffered=True)

#          sql = "select * from teachers where id_no = %s and password = %s"
#          cursor.execute(sql, (id_no, password,))
#          teachers = cursor.fetchone()

#          if teachers:
#             msg = "You already have an account"
#          else:
#             sql = "insert into teachers (id_no, password) values(%s, %s)"
#             cursor.execute(sql, (id_no, password,))
#             cursor.close()
#             db.commit()
#             msg = "You have successfully registered"
#       else:
#          msg = "Fill both id no and password"
#    return render_template("teacher_registration.html", msg=msg)

# @app.route("/teacher_dashboard", methods=["GET", "POST"])
# def teacher_dashboard():
    
#    # return render_template ("teacher_dashboard.html")

#    # cursor = db.cursor(dictionary=True)

#    # if request.method == "POST":

#    #      student_id = request.form.get("student_id")

#    #      subject1 = request.form.get("subject1")
#    #      marks1 = request.form.get("marks1")

#    #      subject2 = request.form.get("subject2")
#    #      marks2 = request.form.get("marks2")

#    #      subject3 = request.form.get("subject3")
#    #      marks3 = request.form.get("marks3")


#    #      subjects_marks = [
#    #          (student_id, subject1, marks1),
#    #          (student_id, subject2, marks2),
#    #          (student_id, subject3, marks3)
#    #      ]


#    #      for record in subjects_marks:

#    #          cursor.execute(
#    #              """
#    #              INSERT INTO marks(student_id, subject, marks)
#    #              VALUES(%s,%s,%s)
#    #              """,
#    #              record
#    #          )

#    #      db.commit()


#    # query = """
#    #  SELECT id, name, roll_no, selected_subjects
#    #  FROM students
#    #  WHERE selected_subjects IS NOT NULL
#    #  """

#    # cursor.execute(query)

#    # students = cursor.fetchall()


#    # for student in students:

#    #      subjects = student["selected_subjects"].split(",")

#    #      student["subject1"] = subjects[0]
#    #      student["subject2"] = subjects[1]
#    #      student["subject3"] = subjects[2]


#    # return render_template(
#    #      "teacher_dashboard.html",
#    #      students=students
#    #  )



#    #  cursor = db.cursor(dictionary=True, buffered=True)

#    #  if request.method == 'POST':

#    #      student_id = request.form.get("student_id")

#    #      subjects = [
#    #          request.form.get("subject1"),
#    #          request.form.get("subject2"),
#    #          request.form.get("subject3")
#    #      ]

#    #      marks = [
#    #          request.form.get("marks1"),
#    #          request.form.get("marks2"),
#    #          request.form.get("marks3")
#    #      ]

#    #      # save marks
#    #      for subject, mark in zip(subjects, marks):

#    #          cursor.execute("""
#    #              SELECT * FROM marks
#    #              WHERE student_id=%s AND subject=%s
#    #          """, (student_id, subject))

#    #          existing = cursor.fetchone()

#    #          if existing:

#    #              cursor.execute("""
#    #                  UPDATE marks
#    #                  SET marks=%s
#    #                  WHERE student_id=%s AND subject=%s
#    #              """, (mark, student_id, subject))

#    #          else:

#    #              cursor.execute("""
#    #                  INSERT INTO marks (student_id, subject, marks)
#    #                  VALUES (%s,%s,%s)
#    #              """, (student_id, subject, mark))

#    #      db.commit()


#    #  # fetch students
#    #  cursor.execute("SELECT * FROM students")
#    # #  cursor.execute("""
#    # #  SELECT id, name, roll_no,
#    # #  IFNULL(selected_subjects, '') AS selected_subjects
#    # #  FROM students
#    # #  """)
#    #  students = cursor.fetchall()


#    #  # fetch all saved marks
#    #  cursor.execute("SELECT * FROM marks")
#    # #  cursor.execute("""
#    # #  SELECT id, name, roll_no,
#    # #  IFNULL(selected_subjects, '') AS selected_subjects
#    # #  FROM students
#    # #  """)
#    #  marks = cursor.fetchall()

#    #  marks_dict = {}

#    #  for m in marks:
#    #      marks_dict[(m["student_id"], m["subject"])] = m["marks"]


#    #  return render_template(
#    #      "teacher_dashboard.html",
#    #      students=students,
#    #      marks_dict=marks_dict
#    #  )

#    # cursor = mysql.connection.cursor(dictionary=True)

#    #  # Get students who selected subjects
#    # cursor.execute("""
#    #      SELECT id, name, roll_no, selected_subjects
#    #      FROM students
#    #      WHERE selected_subjects IS NOT NULL
#    #  """)
#    # students = cursor.fetchall()

#    #  # Get saved marks
#    # cursor.execute("SELECT student_id, subject, marks FROM marks")
#    # marks_data = cursor.fetchall()

#    #  # Convert marks into dictionary
#    # marks = {}

#    # for row in marks_data:
#    #      student_id = row['student_id']
#    #      subject = row['subject']
#    #      mark = row['marks']

#    #      if student_id not in marks:
#    #          marks[student_id] = {}

#    #      marks[student_id][subject] = mark

#    # cursor.close()

#    # return render_template(
#    #      'teacher_dashboard.html',
#    #      students=students,
#    #      marks=marks
#    #  )

#    # cursor = db.cursor(dictionary=True)

#    #  # students with selected subjects
#    # cursor.execute("""
#    #      SELECT id, name, roll_no, selected_subjects
#    #      FROM students
#    #      WHERE selected_subjects IS NOT NULL
#    #  """)
#    # students = cursor.fetchall()

#    #  # fetch saved marks
#    # cursor.execute("SELECT student_id, subject, marks FROM marks")
#    # marks_data = cursor.fetchall()

#    # marks = {}

#    # for row in marks_data:
#    #      student_id = row['student_id']
#    #      subject = row['subject']
#    #      mark = row['marks']

#    #      if student_id not in marks:
#    #          marks[student_id] = {}

#    #      marks[student_id][subject] = mark

#    # cursor.close()

#    # return render_template(
#    #      'teacher_dashboard.html',
#    #      students=students,
#    #      marks=marks
#    #  )


  
#     cursor = db.cursor(dictionary=True, buffered=True)

#     if request.method == 'POST':
        

#         student_id = request.form.get("student_id")

#         subjects = [
#             request.form.get("subject1"),
#             request.form.get("subject2"),
#             request.form.get("subject3")
#         ]

#         marks = [
#             request.form.get("marks1"),
#             request.form.get("marks2"),
#             request.form.get("marks3")
#         ]

#         # save or update marks
#         for subject, mark in zip(subjects, marks):

#             cursor.execute("""
#                 SELECT * FROM marks
#                 WHERE student_id=%s AND subject=%s
#             """, (student_id, subject))

#             existing = cursor.fetchone()

#             if existing:

#                 cursor.execute("""
#                     UPDATE marks
#                     SET marks=%s
#                     WHERE student_id=%s AND subject=%s
#                 """, (mark, student_id, subject))

#             else:

#                 cursor.execute("""
#                     INSERT INTO marks (student_id, subject, marks)
#                     VALUES (%s,%s,%s)
#                 """, (student_id, subject, mark))

#         db.commit()


#     # show only students who selected subjects
#     cursor.execute("""
#         SELECT id, name, roll_no,
#         IFNULL(selected_subjects,'') AS selected_subjects
#         FROM students
#         WHERE selected_subjects IS NOT NULL
#     """)

#     students = cursor.fetchall()


#     # fetch saved marks
#     cursor.execute("SELECT student_id, subject, marks FROM marks")

#     marks_data = cursor.fetchall()
    

#     marks_dict = {}

#     for row in marks_data:
#       marks_dict[(row["student_id"], row["subject"])] = row["marks"]


#     return render_template(
#         "teacher_dashboard.html",
#         students=students,
#         marks_dict=marks_dict
#     )



# if __name__ == "__main__":
#  app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))