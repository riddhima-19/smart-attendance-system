# utils/db_utils.py

import sqlite3

DB_NAME = "college.db"

def get_student_data(college_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM student_info WHERE college_id = ?", (college_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def insert_student_data(student_data):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO student_info 
        (college_id, full_name, course, year, phone_number, email, parents_name, address, profile_photo, face_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', student_data)
    conn.commit()
    conn.close()
