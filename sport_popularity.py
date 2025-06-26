import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "dataBase", "students.db")


def get_sport_popularity(year_filter=None):

    query = """
        SELECT 
            teams.activity,
            COUNT(DISTINCT enrollments.student_id) AS total_enrolled,
            COUNT(attendance_records.record_id) AS total_sessions,
            SUM(CASE WHEN attendance_records.attendance_status = 'Present' THEN 1 ELSE 0 END) AS present_sessions,
            ROUND(
                (SUM(CASE WHEN attendance_records.attendance_status = 'Present' THEN 1 ELSE 0 END) * 100.0) / 
                COUNT(attendance_records.attendance_status)
            , 1) AS attendance_rate,
            teams.year,
            teams.semester
        FROM 
            teams
        LEFT JOIN 
            enrollments ON teams.team_id = enrollments.team_id
        LEFT JOIN 
            attendance_records ON enrollments.enrollment_id = attendance_records.enrollment_id
        LEFT JOIN 
            students ON enrollments.student_id = students.student_id
    """

    params = []
    if year_filter:
        query += " WHERE teams.year = ?"
        params.append(year_filter)

    query += """
        GROUP BY 
            teams.activity, teams.year, teams.semester
        ORDER BY 
            total_enrolled DESC, attendance_rate DESC
    """

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(query, params)
    results = cursor.fetchall()
    connection.close()
    return results