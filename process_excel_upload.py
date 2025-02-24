import sqlite3
import os

DATABASE = os.path.join('database', 'students.db')

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect(DATABASE)  # create database if it doesn't exist
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn


def create_tables():
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                student_name TEXT NOT NULL
            );
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                activity TEXT NOT NULL,
                attendance TEXT NOT NULL,
                date TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students(student_id)
            );
        ''')
        conn.commit()
        conn.close()


# Call the create_tables function to ensure the tables exist
create_tables()
