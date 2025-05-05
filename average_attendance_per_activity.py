

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "dataBase", "students.db")


def activity_attendance(year_ID):
    query = """
            SELECT 
                teams.activity,
                COUNT(DISTINCT students.student_id) AS total_students,
                SUM(CASE WHEN attendance_records.attendance_status = 'Present' THEN 1 ELSE 0 END) AS present_count,
                ROUND(
                    (SUM(CASE WHEN attendance_records.attendance_status = 'Present' THEN 1 ELSE 0 END) * 100.0) / 
                    COUNT(attendance_records.attendance_status)
                , 1) AS attendance_percentage
            FROM 
                attendance_records
            JOIN 
                enrollments ON attendance_records.enrollment_id = enrollments.enrollment_id
            JOIN 
                students ON enrollments.student_id = students.student_id
            JOIN 
                teams ON enrollments.team_id = teams.team_id
            WHERE 
                students.year_group = ?
            GROUP BY 
                teams.activity
            ORDER BY 
                attendance_percentage DESC
        """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    # Using parameterized query prevents SQL injection
    cursor.execute(query, (year_ID,))
    results = cursor.fetchall()
    connection.close()
    return results