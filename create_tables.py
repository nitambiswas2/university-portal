import mysql.connector

db = mysql.connector.connect(
    host="switchback.proxy.rlwy.net",
    user="root",
    password="GPdJgYOVazPKkxpdMZtaeeikxJkLfewI",
    database="railway",
    port=19259
)

cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
   id INT AUTO_INCREMENT PRIMARY KEY,
   roll_no VARCHAR(50),
   password VARCHAR(50),
   name VARCHAR(100),
   photo VARCHAR(200),
   selected_subjects VARCHAR(200)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS teachers (
   id INT AUTO_INCREMENT PRIMARY KEY,
   id_no VARCHAR(50),
   password VARCHAR(50)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS marks (
   id INT AUTO_INCREMENT PRIMARY KEY,
   student_id INT,
   subject VARCHAR(100),
   marks INT
)
""")

db.commit()
print("All tables created successfully!")
cursor.close()
db.close()