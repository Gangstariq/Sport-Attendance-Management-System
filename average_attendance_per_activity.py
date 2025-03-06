import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "dataBase", "students.db")


def activity_attendance(year_ID):
    query = """
        SELECT DISTINCT activity,
               COUNT(CASE WHEN attendance = 'Present' THEN 1 END) AS present_count,
               COUNT(*) AS total_sessions,
               (CAST(COUNT(CASE WHEN attendance = 'Present' THEN 1 END) AS FLOAT) / COUNT(*)) * 100 AS average_attendance_percentage
        FROM attendance_records
        WHERE year = ?
        GROUP BY activity
        ORDER BY average_attendance_percentage DESC;
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(query, (str(year_ID),))
    results = cursor.fetchall()
    connection.close()
    return results