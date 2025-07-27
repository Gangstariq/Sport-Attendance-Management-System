import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dataBase", "students.db")


# def students_attendance(student_ID):
#     """Get all attendance records for a specific student"""
#     query = """
#         SELECT DISTINCT students.student_id, teams.team_name, activity, attendance_status, session_date
#         FROM students, attendance_records, enrollments, teams
#
#         WHERE students.student_id == enrollments.student_id
#         AND enrollments.team_id == teams.team_id
#         AND enrollments.enrollment_id == attendance_records.enrollment_id
#         AND students.student_id = ?
#         order by students.student_id, session_date, team_name, activity
#     """
#     connection = sqlite3.connect(DB_PATH)
#     cursor = connection.cursor()
#     cursor.execute(query, (student_ID,))
#     results = cursor.fetchall()
#
#     # If no exact match found, try pattern matching
#     if not results:
#         cursor.execute(query.replace("AND students.student_id = ?", "AND students.student_id LIKE ?"),
#                        (f"%{student_ID}%",))
#         results = cursor.fetchall()
#
#     connection.close()
#     return results

def students_attendance(student_ID):
    """Get all attendance records for a specific student """
    # Clean the input - remove any whitespace
    student_ID = str(student_ID).strip()

    query = """
        SELECT DISTINCT 
            students.student_id, 
            teams.team_name, 
            activity, 
            attendance_status, 
            session_date
        FROM 
            students, 
            attendance_records, 
            enrollments, 
            teams
        WHERE 
            students.student_id = enrollments.student_id
        AND 
            enrollments.team_id = teams.team_id
        AND 
            enrollments.enrollment_id = attendance_records.enrollment_id
        AND 
            students.student_id = ?
        ORDER BY 
            students.student_id, session_date, team_name, activity
    """


    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(query, (student_ID,))
    results = cursor.fetchall()
    connection.close()

    return results



def get_student_dashboard_data(student_id):
    """
    Get all the data needed for a student's dashboard
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # Get student's overall attendance data
    student_query = """
        SELECT students.full_name, teams.activity,
            COUNT(*) AS total_sessions,
            SUM(CASE WHEN attendance_records.attendance_status = 'Present' THEN 1 ELSE 0 END) AS present_sessions,
            ROUND(
                (SUM(CASE WHEN attendance_records.attendance_status = 'Present' THEN 1 ELSE 0 END) * 100.0) / 
                COUNT(*)
            , 1) AS attendance_percentage
        FROM 
            students
        JOIN 
            enrollments ON students.student_id = enrollments.student_id
        JOIN 
            teams ON enrollments.team_id = teams.team_id
        JOIN 
            attendance_records ON enrollments.enrollment_id = attendance_records.enrollment_id
        WHERE 
            students.student_id = ?
            AND (attendance_records.is_cancelled IS NULL OR attendance_records.is_cancelled != 'Yes')
        GROUP BY 
            students.student_id, students.full_name, teams.activity
    """

    cursor.execute(student_query, (student_id,))
    results = cursor.fetchall()

    if not results:
        connection.close()
        return {
            'student_name': 'Student',
            'overall_attendance': 0,
            'current_sport': 'No sport enrolled',
            'sessions_attended': 0,
            'total_sessions': 0,
            'days_since_absence': 'N/A'
        }

    # Calculate overall stats across all sports
    total_sessions_all = sum(row[2] for row in results)
    present_sessions_all = sum(row[3] for row in results)
    overall_attendance = round((present_sessions_all / total_sessions_all * 100), 1) if total_sessions_all > 0 else 0

    # Get the most recent sport
    current_sport = results[0][1]  # First sport in the list
    student_name = results[0][0]

    # Get days since last absence
    absence_query = """
        SELECT MAX(attendance_records.session_date) as last_absence_date
        FROM 
            attendance_records
        JOIN 
            enrollments ON attendance_records.enrollment_id = enrollments.enrollment_id
        JOIN 
            students ON enrollments.student_id = students.student_id
        WHERE 
            students.student_id = ?
            AND attendance_records.attendance_status IN ('Explained absence', 'Unexplained absence')
            AND (attendance_records.is_cancelled IS NULL OR attendance_records.is_cancelled != 'Yes')
    """

    cursor.execute(absence_query, (student_id,))
    absence_result = cursor.fetchone()

    days_since_absence = 'N/A'
    if absence_result and absence_result[0]:
        try:
            date_str = absence_result[0]
            last_absence = None

            # Try different date formats
            formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d %b %Y', '%d %B %Y']
            for fmt in formats:
                try:
                    last_absence = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue

            if last_absence:
                days_diff = (datetime.now() - last_absence).days
                days_since_absence = f"{days_diff} days"
        except:
            days_since_absence = 'N/A'

    connection.close()

    return {
        'student_name': student_name,
        'overall_attendance': overall_attendance,
        'current_sport': current_sport,
        'sessions_attended': present_sessions_all,
        'total_sessions': total_sessions_all,
        'days_since_absence': days_since_absence
    }