import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dataBase", "students.db")


def daily_attendance_summary(year_ID):
    #basically SUM counts how many were present/abscent that day so adds up all the '1' values
    #Case WHEN is like an if condition so if it was 'present' then set the value to 1 (present) or else o (not present)
    #AS present_count just sets it to like a variable ot make it easier ot reference and renames it
    #CAST converts the date into an integer so its like ordered correctly
    query = """
        SELECT 
            attendance_records.session_date AS formatted_date,
            SUM(CASE WHEN attendance_records.attendance_status = 'Present' THEN 1 ELSE 0 END) AS present_count,
            SUM(CASE WHEN attendance_records.attendance_status = 'Explained absence' THEN 1 ELSE 0 END) AS explained_absence_count,
            SUM(CASE WHEN attendance_records.attendance_status = 'Unexplained absence' THEN 1 ELSE 0 END) AS unexplained_absence_count
        FROM 
            attendance_records
        JOIN 
            enrollments ON attendance_records.enrollment_id = enrollments.enrollment_id
        JOIN 
            students ON enrollments.student_id = students.student_id
        WHERE 
            students.year_group = ?
        GROUP BY 
            attendance_records.session_date
        ORDER BY 
            attendance_records.session_date ASC
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(query, (year_ID,))
    results = cursor.fetchall()
    connection.close()
    return results


def activity_attendance(year_ID):
    #Get average attendance per activity for a specific year group
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
    cursor.execute(query, (year_ID,))
    results = cursor.fetchall()
    connection.close()
    return results


def sport_attendance_by_year(year_ID):
    #Get total sport attendance data by year group
    query = """
        SELECT DISTINCT students.student_id, students.year_group, teams.activity, attendance_records.attendance_status, attendance_records.session_date
        FROM students, attendance_records, enrollments, teams

        WHERE students.student_id = enrollments.student_id
        AND enrollments.team_id = teams.team_id
        AND enrollments.enrollment_id = attendance_records.enrollment_id
        AND students.year_group LIKE ?
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(query, (f"%{year_ID}%",))
    results = cursor.fetchall()

    connection.close()
    return results


def get_teacher_dashboard_data():
    #Get all the data needed for teacher's dashboard

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

    # average attendance for the school
    avg_attendance_query = """
        SELECT 
            ROUND(
                (SUM(CASE WHEN attendance_records.attendance_status = 'Present' THEN 1 ELSE 0 END) * 100.0) / 
                COUNT(attendance_records.attendance_status)
            , 1) AS school_average
        FROM 
            attendance_records
        WHERE 
            (attendance_records.is_cancelled IS NULL OR attendance_records.is_cancelled != 'Yes')
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
                (attendance_records.is_cancelled IS NULL OR attendance_records.is_cancelled != 'Yes')
            GROUP BY 
                students.student_id
            HAVING 
                attendance_percentage < 85
        )
    """
    cursor.execute(below_threshold_query)
    below_threshold = cursor.fetchone()[0]

    # Get last upload time (most recent session date as proxy)
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


def get_sport_popularity(year_filter):
    query = """
        SELECT 
            teams.activity,
            COUNT(DISTINCT enrollments.student_id) AS total_enrolled,
            COUNT(*) AS total_sessions,
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


def perfect_attendance_students(year_filter):
    query = """
        SELECT students.student_id, students.full_name, students.year_group, teams.activity,
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
            (attendance_records.is_cancelled IS NULL OR attendance_records.is_cancelled != 'Yes')
    """

    params = []
    if year_filter:
        query += " AND teams.year = ?"
        params.append(year_filter)

    query += """
        GROUP BY 
            students.student_id, students.full_name, students.year_group, teams.activity
        HAVING 
            attendance_percentage = 100.0
        ORDER BY 
            students.year_group, students.full_name, teams.activity
    """

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(query, params)
    results = cursor.fetchall()
    connection.close()
    return results


def staff_workload_analysis(year_filter):
    #Get staff workload data - handles multiple staff names in one field

    # First, get all the raw data
    query = """
        SELECT 
            attendance_records.staff,
            teams.activity,
            teams.team_name,
            attendance_records.session_date,
            teams.year,
            teams.semester
        FROM 
            attendance_records
        JOIN 
            enrollments ON attendance_records.enrollment_id = enrollments.enrollment_id
        JOIN 
            teams ON enrollments.team_id = teams.team_id
        WHERE 
            attendance_records.staff IS NOT NULL 
            AND attendance_records.staff != ''
    """

    params = []
    if year_filter:
        query += " AND teams.year = ?"
        params.append(year_filter)

    query += " ORDER BY teams.activity, attendance_records.session_date"

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(query, params)
    raw_results = cursor.fetchall()
    connection.close()

    # Process the results to split staff names and count properly
    staff_data = {}  # Will store: {staff_name: {activity: {sessions: count, dates: set, teams: set}}}

    for result in raw_results:
        staff_field = result[0]  # The full staff string like "Daniel Xu, Steve Comninos, Gordan Su"
        activity = result[1]
        team_name = result[2]
        session_date = result[3]
        year = result[4]
        semester = result[5]

        # Split the staff names by comma and clean them up
        if ',' in staff_field:
            staff_names = [name.strip() for name in staff_field.split(',')]
        else:
            staff_names = [staff_field.strip()]

        # Count each staff member individually
        for staff_name in staff_names:
            if staff_name:  # Make sure name isn't empty

                # Initialize staff member if not exists
                if staff_name not in staff_data:
                    staff_data[staff_name] = {}

                # Initialize activity for this staff member if not exists
                activity_key = f"{activity} ({year} S{semester})"
                if activity_key not in staff_data[staff_name]:
                    staff_data[staff_name][activity_key] = {
                        'sessions': 0,
                        'dates': set(),
                        'teams': set(),
                        'year': year,
                        'semester': semester,
                        'activity': activity
                    }

                # Count this session for this staff member
                staff_data[staff_name][activity_key]['sessions'] += 1
                staff_data[staff_name][activity_key]['dates'].add(session_date)
                staff_data[staff_name][activity_key]['teams'].add(team_name)

    # Convert to the format expected by the template
    results = []
    for staff_name, activities in staff_data.items():
        for activity_key, data in activities.items():
            results.append((
                staff_name,  # Staff name
                data['activity'],  # Activity
                data['sessions'],  # Total sessions
                len(data['dates']),  # Unique dates
                len(data['teams']),  # Teams managed
                data['year'],  # Year
                data['semester']  # Semester
            ))

    # Sort by total sessions (descending), then by staff name
    results.sort(key=lambda x: (-x[2], x[0]))

    return results


def low_attendance_students(year_filter, attendance_threshold=85):
    #Get students with attendance rates at or below the threshold
    query = """
        SELECT 
            students.student_id,
            students.full_name,
            students.year_group,
            teams.activity,
            COUNT(*) AS total_sessions,
            SUM(CASE WHEN attendance_records.attendance_status = 'Present' THEN 1 ELSE 0 END) AS present_sessions,
            SUM(CASE WHEN attendance_records.attendance_status = 'Explained absence' THEN 1 ELSE 0 END) AS explained_absences,
            SUM(CASE WHEN attendance_records.attendance_status = 'Unexplained absence' THEN 1 ELSE 0 END) AS unexplained_absences,
            ROUND(
                (SUM(CASE WHEN attendance_records.attendance_status = 'Present' THEN 1 ELSE 0 END) * 100.0) / 
                COUNT(*)
            , 1) AS attendance_percentage,
            teams.year,
            teams.semester
        FROM 
            students
        JOIN 
            enrollments ON students.student_id = enrollments.student_id
        JOIN 
            teams ON enrollments.team_id = teams.team_id
        JOIN 
            attendance_records ON enrollments.enrollment_id = attendance_records.enrollment_id
        WHERE 
            (attendance_records.is_cancelled IS NULL OR attendance_records.is_cancelled != 'Yes')
    """

    params = []
    if year_filter:
        query += " AND teams.year = ?"
        params.append(year_filter)

    query += """
        GROUP BY 
            students.student_id, students.full_name, students.year_group, teams.activity, teams.year, teams.semester
        HAVING 
            attendance_percentage <= ?
        ORDER BY 
            attendance_percentage ASC, students.full_name
    """

    params.append(attendance_threshold)

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(query, params)
    results = cursor.fetchall()
    connection.close()
    return results


def time_slot_effectiveness(year_filter):
    query = """
        SELECT 
            attendance_records.start_time,
            attendance_records.end_time,
            teams.activity,
            COUNT(*) AS total_sessions,
            COUNT(DISTINCT students.student_id) AS unique_students,
            SUM(CASE WHEN attendance_records.attendance_status = 'Present' THEN 1 ELSE 0 END) AS present_count,
            ROUND(
                (SUM(CASE WHEN attendance_records.attendance_status = 'Present' THEN 1 ELSE 0 END) * 100.0) / 
                COUNT(*)
            , 1) AS attendance_rate,
            COUNT(DISTINCT attendance_records.staff) AS staff_count,
            teams.year,
            teams.semester
        FROM 
            attendance_records
        JOIN 
            enrollments ON attendance_records.enrollment_id = enrollments.enrollment_id
        JOIN 
            students ON enrollments.student_id = students.student_id
        JOIN 
            teams ON enrollments.team_id = teams.team_id
        WHERE 
            attendance_records.start_time IS NOT NULL 
            AND attendance_records.end_time IS NOT NULL
    """

    params = []
    if year_filter:
        query += " AND teams.year = ?"
        params.append(year_filter)

    query += """
        GROUP BY 
            attendance_records.start_time, attendance_records.end_time, teams.activity, teams.year, teams.semester
        ORDER BY 
            attendance_records.start_time, attendance_rate DESC
    """

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(query, params)
    results = cursor.fetchall()
    connection.close()
    return results