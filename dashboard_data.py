import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "dataBase", "students.db")


def get_student_dashboard_data(student_id):
    """
    Get all the data needed for a student's dashboard
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # Get student's overall attendance data
    student_query = """
        SELECT students.full_name, teams.activity,
            COUNT(attendance_records.record_id) AS total_sessions,
            SUM(CASE WHEN attendance_records.attendance_status = 'Present' THEN 1 ELSE 0 END) AS present_sessions,
            ROUND(
                (SUM(CASE WHEN attendance_records.attendance_status = 'Present' THEN 1 ELSE 0 END) * 100.0) / 
                COUNT(attendance_records.attendance_status)
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
            AND attendance_records.is_cancelled = 'No'
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

    # Get the most recent sport (you might want to modify this logic)
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
            AND attendance_records.is_cancelled = 'No'
    """

    cursor.execute(absence_query, (student_id,))
    absence_result = cursor.fetchone()

    days_since_absence = 'N/A'
    if absence_result[0]:
        try:
            last_absence = datetime.strptime(absence_result[0], '%Y-%m-%d %H:%M:%S')
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


def get_teacher_dashboard_data():
    """
    Get all the data needed for teacher's dashboard
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # Total number of students
    total_students_query = """
        SELECT COUNT(DISTINCT students.student_id) as total_students
        FROM students
        JOIN enrollments ON students.student_id = enrollments.student_id
    """
    cursor.execute(total_students_query)
    total_students = cursor.fetchone()[0]

    # School-wide average attendance
    avg_attendance_query = """
        SELECT 
            ROUND(
                (SUM(CASE WHEN attendance_records.attendance_status = 'Present' THEN 1 ELSE 0 END) * 100.0) / 
                COUNT(attendance_records.attendance_status)
            , 1) AS school_average
        FROM 
            attendance_records
        WHERE 
            attendance_records.is_cancelled = 'No'
    """
    cursor.execute(avg_attendance_query)
    school_average = cursor.fetchone()[0] or 0

    # Number of active sports
    active_sports_query = """
        SELECT COUNT(DISTINCT teams.activity) as active_sports
        FROM teams
    """
    cursor.execute(active_sports_query)
    active_sports = cursor.fetchone()[0]

    # Students below 85% attendance
    below_threshold_query = """
        SELECT COUNT(*) as below_threshold
        FROM (
            SELECT 
                students.student_id,
                ROUND(
                    (SUM(CASE WHEN attendance_records.attendance_status = 'Present' THEN 1 ELSE 0 END) * 100.0) / 
                    COUNT(attendance_records.attendance_status)
                , 1) AS attendance_percentage
            FROM 
                students
            JOIN 
                enrollments ON students.student_id = enrollments.student_id
            JOIN 
                attendance_records ON enrollments.enrollment_id = attendance_records.enrollment_id
            WHERE 
                attendance_records.is_cancelled = 'No'
            GROUP BY 
                students.student_id
            HAVING 
                attendance_percentage < 85
        )
    """
    cursor.execute(below_threshold_query)
    below_threshold = cursor.fetchone()[0]

    # Get last upload time (this is a bit tricky since we don't track upload times)
    # For now, we'll get the most recent session date as a proxy
    last_activity_query = """
        SELECT MAX(attendance_records.session_date) as last_activity
        FROM attendance_records
    """
    cursor.execute(last_activity_query)
    last_activity_result = cursor.fetchone()[0]

    last_upload = 'No recent activity'
    if last_activity_result:
        try:
            last_date = datetime.strptime(last_activity_result, '%Y-%m-%d %H:%M:%S')
            days_ago = (datetime.now() - last_date).days
            if days_ago == 0:
                last_upload = 'Today'
            elif days_ago == 1:
                last_upload = 'Yesterday'
            else:
                last_upload = f'{days_ago} days ago'
        except:
            last_upload = 'Unknown'

    connection.close()

    return {
        'total_students': total_students,
        'school_average': school_average,
        'active_sports': active_sports,
        'below_threshold': below_threshold,
        'last_upload': last_upload
    }