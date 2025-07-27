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


    connection.close()

    return {
        'total_students': total_students,
        'school_average': school_average,
        'active_sports': active_sports,
        'below_threshold': below_threshold,
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


def attendance_streak_tracker(year_filter):
#finds the streaks of all students

    # gets all student attendance information
    query = """
        SELECT 
            students.student_id,
            students.full_name,
            students.year_group,
            attendance_records.session_date,
            attendance_records.attendance_status
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
        ORDER BY 
            students.student_id, attendance_records.session_date
    """

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(query, params)
    all_records = cursor.fetchall()
    connection.close()

    # create empty lists for student data to be found
    student_streaks = []
    current_student = None
    student_dates = []

    #looping thru sql query and setting all the variables up
    for record in all_records:
        student_id = record[0]
        student_name = record[1]
        year_group = record[2]
        session_date = record[3]
        attendance_status = record[4]


        if current_student != student_id:
            if current_student is not None:
                # Calculate streaks for the previous student
                streak_info = calculate_student_streaks(current_student, current_name, current_year, student_dates)
                if streak_info:
                    student_streaks.append(streak_info)


            current_student = student_id
            current_name = student_name
            current_year = year_group
            student_dates = []


        student_dates.append({
            'date': session_date,
            'status': attendance_status
        })

    # checking last student
    if current_student is not None:
        streak_info = calculate_student_streaks(current_student, current_name, current_year, student_dates)
        if streak_info:
            student_streaks.append(streak_info)

    return student_streaks


def calculate_student_streaks(student_id, student_name, year_group, student_dates):
#calcultes the current steak a student has and their longest streak
    if not student_dates:
        return None

    unique_dates = [] #stores each date + and if student was present or not
    date_statuses = {} #storing multiple attended sessions in a signle date to check at least one was present

    #go through every session attended by studetn
    for session in student_dates:
        date = session['date'][:10]
        status = session['status']

        # For each date, store all attendance statuses
        if date not in date_statuses:
            date_statuses[date] = [] # makee a new list for this date
        date_statuses[date].append(status)

    #go through the list of all dates and check if present for at least one of the sessions
    for date in date_statuses:
        statuses_for_day = date_statuses[date]
        is_present_today = False

        for status in statuses_for_day:
            if status == "Present":
                is_present_today = True
                break
        #after checking if present at least one it adds to unique_dates a dictionary
        unique_dates.append({
            'date': date,
            'present': is_present_today
        })

    # sort dates in order
    unique_dates.sort(key=lambda x: x['date'])

    # find the current streak by starting from most recent date (last one) to the earliers date
    current_streak = 0


    for i in range(len(unique_dates) - 1, -1, -1):
        if unique_dates[i]['present']:
            current_streak += 1
        else:
            break

    # find longest streak
    longest_streak = 0
    temp_streak = 0

    for date_info in unique_dates:
        if date_info['present']:
            temp_streak += 1
            if temp_streak > longest_streak:
                longest_streak = temp_streak
        else:
            temp_streak = 0


    return {
        'student_id': student_id,
        'student_name': student_name,
        'year_group': year_group,
        'current_streak': current_streak,
        'longest_streak': longest_streak,
        'total_days': len(unique_dates)
    }


def get_single_student_attendance(student_id):
    # gets all student attendance information
    query = """
        SELECT 
            students.full_name,
            students.year_group,
            attendance_records.session_date,
            attendance_records.attendance_status
        FROM 
            students
        JOIN 
            enrollments ON students.student_id = enrollments.student_id
        JOIN 
            teams ON enrollments.team_id = teams.team_id
        JOIN 
            attendance_records ON enrollments.enrollment_id = attendance_records.enrollment_id
        WHERE 
            students.student_id = ? AND
            (attendance_records.is_cancelled IS NULL OR attendance_records.is_cancelled != 'Yes')
        ORDER BY 
            attendance_records.session_date
    """

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(query, (student_id,))
    results = cursor.fetchall()
    connection.close()

    if not results:
        return None

    first_row = results[0]
    student_name = first_row[0]
    year_group = first_row[1]



    student_dates = []
    for row in results:
        session_date = row[2]
        attendance_status = row[3]
        student_dates.append({
            'date': session_date,
            'status': attendance_status
        })

    streak_data = calculate_student_streaks(student_id, student_name, year_group, student_dates)

    return streak_data


def get_available_teams(year_filter=None, semester_filter=None, activity_filter=None):
    """Get list of available teams based on filters"""
    query = """
        SELECT DISTINCT 
            teams.year,
            teams.semester, 
            teams.activity,
            teams.team_name,
            teams.team_id,
            COUNT(DISTINCT enrollments.student_id) as student_count
        FROM 
            teams
        LEFT JOIN 
            enrollments ON teams.team_id = enrollments.team_id
        WHERE 1=1
    """

    params = []

    if year_filter:
        query += " AND teams.year = ?"
        params.append(year_filter)

    if semester_filter:
        query += " AND teams.semester = ?"
        params.append(semester_filter)

    if activity_filter:
        query += " AND teams.activity = ?"
        params.append(activity_filter)

    query += """
        GROUP BY 
            teams.team_id, teams.year, teams.semester, teams.activity, teams.team_name
        ORDER BY 
            teams.year DESC, teams.semester, teams.activity, teams.team_name
    """

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(query, params)
    results = cursor.fetchall()
    connection.close()
    return results


def get_team_attendance_data(team_id):
    """Get detailed attendance data for a specific team"""
    query = """
        SELECT 
            students.student_id,
            students.full_name,
            students.year_group,
            teams.team_name,
            teams.activity,
            teams.year,
            teams.semester,
            attendance_records.session_date,
            attendance_records.attendance_status,
            attendance_records.session_name
        FROM 
            students
        JOIN 
            enrollments ON students.student_id = enrollments.student_id
        JOIN 
            teams ON enrollments.team_id = teams.team_id
        JOIN 
            attendance_records ON enrollments.enrollment_id = attendance_records.enrollment_id
        WHERE 
            teams.team_id = ? AND
            (attendance_records.is_cancelled IS NULL OR attendance_records.is_cancelled != 'Yes')
        ORDER BY 
            students.full_name, attendance_records.session_date
    """

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(query, (team_id,))
    results = cursor.fetchall()
    connection.close()
    return results


def get_team_summary_stats(team_id):
    """Get summary statistics for a team"""
    query = """
        SELECT 
            teams.team_name,
            teams.activity,
            teams.year,
            teams.semester,
            COUNT(DISTINCT students.student_id) as total_players,
            COUNT(attendance_records.attendance_status) as total_sessions,
            SUM(CASE WHEN attendance_records.attendance_status = 'Present' THEN 1 ELSE 0 END) as present_count,
            SUM(CASE WHEN attendance_records.attendance_status = 'Explained absence' THEN 1 ELSE 0 END) as explained_count,
            SUM(CASE WHEN attendance_records.attendance_status = 'Unexplained absence' THEN 1 ELSE 0 END) as unexplained_count,
            ROUND(
                (SUM(CASE WHEN attendance_records.attendance_status = 'Present' THEN 1 ELSE 0 END) * 100.0) / 
                COUNT(attendance_records.attendance_status)
            , 1) AS team_attendance_rate
        FROM 
            teams
        JOIN 
            enrollments ON teams.team_id = enrollments.team_id
        JOIN 
            students ON enrollments.student_id = students.student_id
        JOIN 
            attendance_records ON enrollments.enrollment_id = attendance_records.enrollment_id
        WHERE 
            teams.team_id = ? AND
            (attendance_records.is_cancelled IS NULL OR attendance_records.is_cancelled != 'Yes')
        GROUP BY 
            teams.team_id
    """

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(query, (team_id,))
    result = cursor.fetchone()
    connection.close()
    return result


def get_team_player_stats(team_id):
    """Get individual player statistics for a team"""
    query = """
        SELECT 
            students.student_id,
            students.full_name,
            students.year_group,
            COUNT(attendance_records.attendance_status) as total_sessions,
            SUM(CASE WHEN attendance_records.attendance_status = 'Present' THEN 1 ELSE 0 END) as present_sessions,
            SUM(CASE WHEN attendance_records.attendance_status = 'Explained absence' THEN 1 ELSE 0 END) as explained_absences,
            SUM(CASE WHEN attendance_records.attendance_status = 'Unexplained absence' THEN 1 ELSE 0 END) as unexplained_absences,
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
            teams.team_id = ? AND
            (attendance_records.is_cancelled IS NULL OR attendance_records.is_cancelled != 'Yes')
        GROUP BY 
            students.student_id, students.full_name, students.year_group
        ORDER BY 
            attendance_percentage DESC, students.full_name
    """

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(query, (team_id,))
    results = cursor.fetchall()
    connection.close()
    return results


def get_unique_filter_options():
    """Get unique years, semesters, and activities for filter dropdowns"""
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # Get unique years
    cursor.execute("SELECT DISTINCT year FROM teams ORDER BY year DESC")
    years = [row[0] for row in cursor.fetchall()]

    # Get unique semesters
    cursor.execute("SELECT DISTINCT semester FROM teams ORDER BY semester")
    semesters = [row[0] for row in cursor.fetchall()]

    # Get unique activities
    cursor.execute("SELECT DISTINCT activity FROM teams ORDER BY activity")
    activities = [row[0] for row in cursor.fetchall()]

    connection.close()

    return {
        'years': years,
        'semesters': semesters,
        'activities': activities
    }