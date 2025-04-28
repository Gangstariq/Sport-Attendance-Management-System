import sqlite3
import os

DATABASE = os.path.join('dataBase', 'students.db')

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect(DATABASE)  # create database if it doesn't exist
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn


# def create_tables():
#     conn = create_connection()
#     if conn:
#         cursor = conn.cursor()
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS students (
#                 student_id TEXT PRIMARY KEY,
#                 student_name TEXT NOT NULL
#             );
#         ''')
#
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS attendance_records (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 student_id TEXT NOT NULL,
#                 activity TEXT NOT NULL,
#                 attendance TEXT NOT NULL,
#                 date TEXT NOT NULL,
#                 year TEXT NOT NULL,
#                 FOREIGN KEY (student_id) REFERENCES students(student_id)
#             );
#         ''')
#         conn.commit()
#         conn.close()

def create_tables():
    conn = create_connection()
    if conn:
        cursor = conn.cursor()

        # A temporary table to store the data from the spreadsheet
        cursor.execute('''
                    CREATE TABLE IF NOT EXISTS staging_full_data (
                        student_id TEXT,
                        student_name TEXT,
                        year TEXT,
                        boarder TEXT,
                        house TEXT,
                        homeroom TEXT,
                        campus TEXT,
                        gender TEXT,
                        birthdate TEXT,
                        secondary TEXT,
                        email TEXT,
                        team TEXT,
                        activity TEXT,
                        session TEXT,
                        date TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        session_staff TEXT,
                        attendance TEXT,
                        for_fixture TEXT,
                        flags TEXT,
                        cancelled TEXT
                    );
                ''')

        # Students table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                year_group TEXT NOT NULL,
                is_boarder TEXT NOT NULL CHECK (is_boarder IN ('Yes', 'No')),
                house TEXT NOT NULL,
                homeroom TEXT NOT NULL,
                campus TEXT,
                gender TEXT NOT NULL CHECK (gender IN ('male', 'female')),
                birth_date TEXT NOT NULL,
                email TEXT NOT NULL
            );
        ''')

        # Teams table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teams (
                team_id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_name TEXT,
                activity TEXT NOT NULL,
                semester INTEGER NOT NULL CHECK (semester IN (1, 2)),
                year INTEGER NOT NULL,
                head_coach TEXT
            );
        ''')

        # Enrollments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enrollments (
                enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                team_id INTEGER NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students(student_id),
                FOREIGN KEY (team_id) REFERENCES teams(team_id)
            );
        ''')

        # Attendance records table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance_records (
                record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                enrollment_id INTEGER NOT NULL,
                session_name TEXT NOT NULL,
                session_date TEXT NOT NULL,
                start_time TEXT NOT NULL, -- need to think about making a formatting constraint for this
                end_time TEXT NOT NULL, -- need to think about making a formatting constraint for this
                staff TEXT,
                attendance_status TEXT NOT NULL CHECK (attendance_status IN ('Present', 'Unexplained absence', 'Explained absence')),
                is_fixture TEXT NOT NULL CHECK (is_fixture IN ('Yes', 'No')),
                has_flags TEXT CHECK (has_flags IN ('Yes', 'No')),
                is_cancelled TEXT NOT NULL CHECK (is_cancelled IN ('Yes', 'No')),
                FOREIGN KEY (enrollment_id) REFERENCES enrollments(enrollment_id)
            );
        ''')
        conn.close()

# Create the tables
create_tables()

# Call it
create_tables()




# Call the create_tables function to ensure the tables exist
create_tables()
