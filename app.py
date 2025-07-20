from flask import Flask, render_template, request, jsonify, session
import sqlite3
import os
from werkzeug.utils import secure_filename
from openpyxl import load_workbook
import plotly.graph_objs as go
import datetime
import plotly.io as pio
import openpyxl
from flask_oidc import OpenIDConnect
from flask import Flask, redirect, url_for

#imports of other python functions:
from functions.student_services import students_attendance, get_student_dashboard_data
from functions.teacher_services import daily_attendance_summary, activity_attendance, sport_attendance_by_year, get_teacher_dashboard_data, get_sport_popularity, perfect_attendance_students, staff_workload_analysis, low_attendance_students




import process_excel_upload
from process_excel_upload import create_connection

app = Flask(__name__)
app.secret_key = "hgytdytdtrds324strcd"

app.config["DATABASE_PATH"] = os.path.join(app.root_path, "dataBase")



#copied auth code for sbhs login page
app.config["OIDC_CLIENT_SECRETS"] = "client_secrets.json"
# This HAS to match the registered scopes
app.config["OIDC_SCOPES"] = "openid profile"
# Prefix the routes added by this library to prevent any
# collisions with our routes.
oidc = OpenIDConnect(app, prefix="/oidc/")

#Functions NOT related to routing
def parse_date_flexible(date_string):
#    Takes in date string which can be multiple formats
#    and converst them into a datetime object

# all possible date formats to try
    date_formats = [
        '%Y-%m-%d %H:%M:%S',  #Type 1 (Large dataset format): "2024-11-09 14:30:00"
        '%d %b %Y',  #Type 2 (Old realistic data format): "9 Nov 2024"
        '%d-%m-%Y',  #Type3: "09-11-2024"
        '%Y-%m-%d',  #Typ 4 : "2024-11-09"
        '%d/%m/%Y',  #Type 5: "09/11/2024"
        '%m/%d/%Y',  #Type 6: "11/09/2024"
        '%d %B %Y',  #Type 7: "9 November 2024"
    ]

# Try each format until one works
    for dateformat in date_formats:
        try:
            return datetime.datetime.strptime(date_string, dateformat)
        except ValueError: #Keep trying if the datetime doesn't work
            continue

    # if none of them work then send an error
    raise ValueError(f"Could not take in data in format: '{date_string}'. Supported formats: {date_formats}")

def parse_time_flexible(time_string):

#    Does the same thing as date but for time
#    and then returns time object

# all possible time formats
    time_formats = [
        '%I:%M%p',  # Original: "2:30PM"
        '%H:%M',  # 24-hour: "14:30"
        '%I:%M %p',  # With space: "2:30 PM"
        '%H:%M:%S',  # With seconds: "14:30:00"
    ]

# reiterate through all formats till one works
    for timeformat in time_formats:
        try:
            return datetime.datetime.strptime(time_string, timeformat).time()
        except ValueError:
            continue

    # If none work, return a default time
    print(f"System was not able to take in the format of '{time_string}', using default 12:00 PM")
    return datetime.time(12, 0)  # Default to 12:00 PM

def parse_excel_row_flexible(row):
#function basically lets me use both small and large excel sheet as one starts with ID and other starts with Name

    if row[0]:
        first_value = str(row[0])
    else:
        first_value = ""
    if row[1]:
        second_value = str(row[1])
    else:
        second_value = ""


    if first_value.isdigit(): #checks if its a digit, if it is assign these variables
        (
            student_id, full_name, year, boarder, house, homeroom,
            campus, gender, birthdate, secondary, email, team, activity,
            session, date, start_time, end_time, session_staff, attendance,
            for_fixture, flags, cancelled
        ) = row
    else: #if starts with name then assign these variables
        (
            full_name, student_id, year, boarder, house, homeroom,
            campus, gender, birthdate, secondary, email, team, activity,
            session, date, start_time, end_time, session_staff, attendance,
            for_fixture, flags, cancelled
        ) = row


    return ( #hence return the way the code takes it after the assignment
        student_id, full_name, year, boarder, house, homeroom,
        campus, gender, birthdate, secondary, email, team, activity,
        session, date, start_time, end_time, session_staff, attendance,
        for_fixture, flags, cancelled
    )
#Routing:
@app.route('/', methods=['GET'])
def home():
    # Check if user is already logged in
    if oidc.user_loggedin:
        oidc_profile = session.get("oidc_auth_profile")

        if oidc_profile:
            # Check if user is a student
            if "student_id" in oidc_profile:
                return redirect("/student-dashboard")
            else:
                # Assume teacher/staff if not a student
                return redirect("/teacher-dashboard")

    # If not logged in, show the login page
    return render_template('home.html')

@app.route('/logout')
def logout_simple():
    oidc.logout()
    session.clear()
    return redirect("/")



@app.route('/teacher-dashboard')
def teacher_dashboard():
    # if not oidc.user_loggedin:
    #     return redirect("/")
    #
    # oidc_profile = session.get("oidc_auth_profile")
    # if "student_id" in oidc_profile:
    #     return redirect("/student-dashboard")  # Wrong user type
    #
    # # Get teacher info from profile
    # teacher_name = oidc_profile.get('name', 'Teacher')
    #
    # # Get real data from database
    dashboard_data = get_teacher_dashboard_data()
    #
    # return render_template('Teacher/teacher-dashboard.html',
    #                        teacher_name=teacher_name,
    #                        **dashboard_data)
    return render_template('Teacher/teacher-dashboard.html', **dashboard_data)


@app.route('/daily-attendance-dashboard', methods=['GET', 'POST'])
def daily_attendance_dashboard():
    results = []
    year_ID = ""

    if request.method == 'POST':
        year_ID = request.form.get('year_ID', '')
        results = daily_attendance_summary(year_ID)  # Call function from external file

    return render_template('Teacher/daily-attendance-dashboard.html', results=results, year_ID=year_ID)
@app.route('/daily-attendance-dashboard-graph', methods=['GET', 'POST'])
def daily_attendance_graph():
    results = []
    graph_html = ""
    year_ID = ""

    if request.method == 'POST':
        # Get the year_ID from the form input
        year_ID = request.form.get('year_ID', '')
        results = daily_attendance_summary(year_ID)  # Fetch data from DB

        if results:
            # Extract data for the graph
            dates = [record[0] for record in results]  # Date column
            present_counts = [record[1] for record in results]  # Present students count
            explained_abs_counts = [record[2] for record in results]  # Explained absences
            unexplained_abs_counts = [record[3] for record in results]  # Unexplained absences

            # Create Plotly Line Graph
            fig = go.Figure()

            fig.add_trace(go.Scatter(x=dates, y=present_counts, mode='lines+markers', name="Present", line=dict(color='green')))
            fig.add_trace(go.Scatter(x=dates, y=explained_abs_counts, mode='lines+markers', name="Explained Absence", line=dict(color='orange')))
            fig.add_trace(go.Scatter(x=dates, y=unexplained_abs_counts, mode='lines+markers', name="Unexplained Absence", line=dict(color='red')))

            # Layout Settings
            fig.update_layout(
                title=f'Daily Attendance Trends for {year_ID}',
                xaxis_title='Date',
                yaxis_title='Number of Students',
                xaxis=dict(type='category')  # Ensures dates display properly
            )

            graph_html = fig.to_html(full_html=False)

    return render_template('Teacher/daily-attendance-dashboard.html', results=results, graph_html=graph_html, year_ID=year_ID)


@app.route('/average-attendance-per-activity', methods=['GET', 'POST'])
def average_attendance_per_activity():
    results = []
    year_ID = ""

    if request.method == 'POST':
        year_ID = request.form.get('year_ID', '')
        results = activity_attendance(year_ID)

    return render_template('Teacher/average-attendance-per-activity.html', results=results, year_ID=year_ID)
@app.route('/average-attendance-per-activity-graph', methods=['GET', 'POST'])
def average_attendance_per_activity_graph():
    results = []
    graph_html = ""
    year_ID = ""

    if request.method == 'POST':
        # Get the year_ID from the form input
        year_ID = request.form.get('year_ID', '')
        # Sanitize input to prevent injection
        year_ID = year_ID.strip()

        results = activity_attendance(year_ID)

        if results:
            activities = [record[0] for record in results]  # Activity names
            attendance_percentages = [record[3] for record in results]  # Average attendance percentages

            # Create Plotly Bar Graph for Average Attendance per Activity
            fig = go.Figure()

            fig.add_trace(go.Bar(x=activities, y=attendance_percentages, name="Average Attendance"))

            # Layout Settings
            fig.update_layout(
                title=f'Average Attendance per Activity for {year_ID}',
                xaxis_title='Activity',
                yaxis_title='Average Attendance (%)',
                xaxis_tickangle=-45  # Rotates the activity names for better visibility
            )

            graph_html = fig.to_html(full_html=False)

    return render_template('Teacher/average-attendance-per-activity.html', results=results, graph_html=graph_html,
                           year_ID=year_ID)

@app.route('/individual_student_attendance', methods=['GET', 'POST'])
def individual_student_attendance():
    results = []
    graph_html = ""
    if request.method == 'POST':
        search_ID = request.form.get('search_ID', '')
        results = students_attendance(search_ID)

    # for my own reference
    # record[0] = student_id
    # record[1] = team
    # record[2] = activity
    # record[3] = attendance (Present, Absent, late?)
    # record[4] = date

    # creates attendence graph if we have data
    if results:
        #gets attendance data by date
        dates = [record[4] for record in results] # date - referenced above "for my own reference"
        statuses = [record[3] for record in results] # attendence

        # makes bar chart data
        attendance_count = {"Present": 0, "Explained absence": 0, "Unexplained absence": 0}
        for status in statuses:
            if status in attendance_count:  # Only count if it's one of the two statuses
                attendance_count[status] += 1

        # ploty graph creation
        data = [
            go.Bar(
                x=list(attendance_count.keys()),
                y=list(attendance_count.values()),
                marker=dict(color=['green', 'red', 'orange'])
            )
        ]
        #green = present
        #red = away
        #orange = late

        #titlting for x and y axis and graph
        layout = go.Layout(
            title=f'Attendance Summary for Student {search_ID}', # title
            xaxis=dict(title='Status'),
            yaxis=dict(title='Count')
        )

        fig = go.Figure(data=data, layout=layout)
        graph_html = fig.to_html(full_html=False)

    return render_template('Teacher/individual_student_attendance.html', results=results, graph_html=graph_html) #converst graph to html graph






@app.route('/sport-popularity', methods=['GET', 'POST'])
def sport_popularity():
    results = []
    year_filter = ""

    if request.method == 'POST':
        year_filter = request.form.get('year_filter', '').strip()  # Changed from year_ID to year_filter

        # Convert to int if provided and not empty, otherwise None
        if year_filter and year_filter != '':
            try:
                year_filter_int = int(year_filter)
            except ValueError:
                year_filter_int = None
        else:
            year_filter_int = None

        results = get_sport_popularity(year_filter_int)

    return render_template('Teacher/sport-popularity.html', results=results,
                           year_filter=year_filter)  # Changed year_ID to year_filter


@app.route('/sport-popularity-graph', methods=['GET', 'POST'])
def sport_popularity_graph():
    results = []
    graph_html = ""
    year_filter = ""

    if request.method == 'POST':
        year_filter = request.form.get('year_filter', '').strip()  # Changed from year_ID to year_filter

        # Convert to int if provided and not empty, otherwise None
        if year_filter and year_filter != '':
            try:
                year_filter_int = int(year_filter)
            except ValueError:
                year_filter_int = None
        else:
            year_filter_int = None

        results = get_sport_popularity(year_filter_int)

        if results:
            sports = [record[0] for record in results]  # Activity names
            enrollments = [record[1] for record in results]  # Total enrolled

            # Create Plotly Bar Graph for Sport Popularity
            fig = go.Figure()

            fig.add_trace(go.Bar(x=sports, y=enrollments, name="Students Enrolled"))

            # Layout Settings
            title_text = f'Sport Popularity for {year_filter}' if year_filter else 'Sport Popularity - All Years'  # Changed year_ID to year_filter
            fig.update_layout(
                title=title_text,
                xaxis_title='Sports/Activities',
                yaxis_title='Number of Students Enrolled',
                xaxis_tickangle=-45
            )

            graph_html = fig.to_html(full_html=False)

    return render_template('Teacher/sport-popularity.html', results=results, graph_html=graph_html,
                           year_filter=year_filter)  # Changed year_ID to year_filter


@app.route('/perfect-attendance', methods=['GET', 'POST'])
def perfect_attendance():
    results = []
    year_ID = ""
    unique_students = 0
    unique_sports = 0

    if request.method == 'POST':
        year_ID = request.form.get('year_ID', '')
        # Convert to int if provided, otherwise None for the function
        year_filter = int(year_ID) if year_ID else None
        results = perfect_attendance_students(year_filter)

        # Calculate summary stats
        if results:
            # Count unique students (some students might be in multiple sports)
            student_ids = []
            sports = []

            for result in results:
                if result[0] not in student_ids:  # result[0] is student_id
                    student_ids.append(result[0])
                if result[3] not in sports:  # result[3] is activity
                    sports.append(result[3])

            unique_students = len(student_ids)
            unique_sports = len(sports)

    return render_template('Teacher/perfect-attendance.html',
                           results=results,
                           year_ID=year_ID,
                           unique_students=unique_students,
                           unique_sports=unique_sports)


@app.route('/staff-workload', methods=['GET', 'POST'])
def staff_workload():
    results = []
    year_filter = ""

    if request.method == 'POST':
        year_filter = request.form.get('year_filter', '').strip()

        # Convert to int if provided and not empty, otherwise None
        if year_filter and year_filter != '':
            try:
                year_filter_int = int(year_filter)
            except ValueError:
                year_filter_int = None
        else:
            year_filter_int = None

        results = staff_workload_analysis(year_filter_int)

    return render_template('Teacher/staff-workload.html', results=results, year_filter=year_filter)
@app.route('/staff-workload-graph', methods=['POST'])
def staff_workload_graph():
    year_filter = request.form.get('year_filter', '').strip()

    # Convert to int if provided and not empty, otherwise None
    if year_filter and year_filter != '':
        try:
            year_filter_int = int(year_filter)
        except ValueError:
            year_filter_int = None
    else:
        year_filter_int = None

    results = staff_workload_analysis(year_filter_int)
    graph_html = ""

    if results:
        # Group by staff member to get total sessions per staff
        staff_totals = {}
        for result in results:
            staff_name = result[0]  # Staff name
            sessions = result[2]  # Total sessions

            if staff_name in staff_totals:
                staff_totals[staff_name] += sessions
            else:
                staff_totals[staff_name] = sessions

        # Get top 15 staff members by workload
        sorted_staff = sorted(staff_totals.items(), key=lambda x: x[1], reverse=True)[:15]

        staff_names = [item[0] for item in sorted_staff]
        session_counts = [item[1] for item in sorted_staff]

        # Create Plotly Bar Graph
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=staff_names,
            y=session_counts,
            name="Total Sessions",
            marker=dict(color='lightcoral')
        ))

        # Layout Settings
        title_text = f'Staff Workload - Top 15 Staff Members'
        if year_filter:
            title_text += f' ({year_filter})'

        fig.update_layout(
            title=title_text,
            xaxis_title='Staff Members',
            yaxis_title='Total Sessions Managed',
            xaxis_tickangle=-45
        )

        graph_html = fig.to_html(full_html=False)

    return render_template('Teacher/staff-workload.html',
                           results=results,
                           year_filter=year_filter,
                           graph_html=graph_html)


@app.route('/low-attendance', methods=['GET', 'POST'])
def low_attendance():
    results = []
    year_filter = ""
    attendance_threshold = 80
    total_flagged = 0
    avg_attendance_rate = 0
    lowest_attendance_rate = 100

    if request.method == 'POST':
        year_filter = request.form.get('year_filter', '').strip()
        attendance_threshold = request.form.get('attendance_threshold', '80').strip()

        # Convert inputs
        year_filter_int = None
        if year_filter and year_filter != '':
            try:
                year_filter_int = int(year_filter)
            except ValueError:
                year_filter_int = None

        try:
            attendance_threshold = int(attendance_threshold)
        except ValueError:
            attendance_threshold = 80

        results = low_attendance_students(year_filter_int, attendance_threshold)

        # Calculate summary stats
        if results:
            total_flagged = len(results)
            attendance_rates = [result[8] for result in results]  # attendance_percentage is at index 8
            avg_attendance_rate = round(sum(attendance_rates) / len(attendance_rates), 1)
            lowest_attendance_rate = min(attendance_rates)

    return render_template('Teacher/low-attendance.html',
                           results=results,
                           year_filter=year_filter,
                           attendance_threshold=attendance_threshold,
                           total_flagged=total_flagged,
                           avg_attendance_rate=avg_attendance_rate,
                           lowest_attendance_rate=lowest_attendance_rate)




@app.route("/student-login")
def student_login_redirect():
    if oidc.user_loggedin:
        oidc_profile = session.get("oidc_auth_profile")

        # Teachers can potentially log in through the school's OIDC server
        # as well, but we only want students.
        if oidc_profile:
            # Check if user is a student
            if "student_id" in oidc_profile:
                return redirect("/student-dashboard")
            else: #todo NEED TO FIGURE OUT WHICH OIDC RESULT IS TEACHER AND NOT JUST IF NOT STUDENT LOGIC CHANGEEE - MAYBE DELTE
                # Teacher/staff redirect
                return redirect("/teacher-dashboard")
    else:
        # Redirect to  login, then come back to home page
        return oidc.redirect_to_auth_server("/")
@app.route('/student-dashboard')
def student_dashboard():
    # Uncomment these when ready to use authentication
    # if not oidc.user_loggedin:
    #     return redirect("/")
    #
    oidc_profile = session.get("oidc_auth_profile")
    # if "student_id" not in oidc_profile:
    #     return redirect("/teacher-dashboard")  # Wrong user type
    #
    # student_id = oidc_profile.get('student_id', 'Unknown')

    # forceful student id for testing
    student_id = "443194182"  # from the anon excel sheet

    # Get student info from profile
    #student_id = oidc_profile.get('student_id', 'Unknown')

    # Get student dashboard data
    dashboard_data = get_student_dashboard_data(student_id)

    # Get student's own attendance for graph
    my_attendance_data = students_attendance(student_id)
    my_attendance_graph = ""

    if my_attendance_data:
        # Create attendance graph for this student
        statuses = [record[3] for record in my_attendance_data]
        attendance_count = {"Present": 0, "Explained absence": 0, "Unexplained absence": 0}

        for status in statuses:
            if status in attendance_count:
                attendance_count[status] += 1

        # Create Plotly graph
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=list(attendance_count.keys()),
            y=list(attendance_count.values()),
            marker=dict(color=['green', 'orange', 'red'])
        ))

        fig.update_layout(
            title=f'My Attendance Summary',
            xaxis_title='Status',
            yaxis_title='Count',
            height=400
        )

        my_attendance_graph = fig.to_html(full_html=False)

    # Get recent sessions (last 10)
    recent_sessions = my_attendance_data[-10:] if my_attendance_data else []

    return render_template('Student access/student-dashboard.html',
                           student_id=student_id,
                           my_attendance_graph=my_attendance_graph,
                           recent_sessions=recent_sessions,
                           **dashboard_data)

















def normalise_and_insert_data():
    conn = create_connection()
    cursor = conn.cursor()



    #important to order by date so that we read the most recent records first
    cursor.execute('SELECT * FROM staging_full_data '
                   'ORDER BY date DESC')

    rows = cursor.fetchall()



    student_cache = set()
    team_cache = set()
    enrollment_cache = set()
    attendance_cache = set()


    #iterate through each row of data
    for row in rows:
        (
            student_id, full_name, year, boarder, house, homeroom,
            campus, gender, birthdate, secondary, email, team, activity,
            session, date, start_time, end_time, session_staff, attendance,
            for_fixture, flags, cancelled
        ) = parse_excel_row_flexible(row)
        # add all unique students to the student table
        if student_id not in student_cache:
            #write this student into the student table
            cursor.execute('''
                INSERT INTO students (student_id, full_name, 
                year_group, is_boarder, house, homeroom, 
                campus, gender, birth_date, email) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (student_id, full_name,
                year, boarder, house, homeroom,
                campus, gender, birthdate, email))

            conn.commit()

            #put the student ID into the cache so that we dont write this student again
            student_cache.add(student_id)

        # add all unique teams to the team table
        team_semester = None
        team_year = None
        date_converted = parse_date_flexible(str(date))
        team_year = date_converted.year
        if date_converted.month <= 6:
            team_semester = 1
        else:
            team_semester = 2

        team_key = (team, activity, team_year, team_semester)
        if team_key not in team_cache:
            # added logic to add teams to the team sql table
            cursor.execute('''
                INSERT INTO teams (team_name, activity, semester, year)
                VALUES (?, ?, ?, ?)
            ''', (team, activity, team_semester, team_year))

            conn.commit()
            team_cache.add(team_key)

        # find team_id
        cursor.execute('''
            SELECT team_id FROM teams
            WHERE team_name = ? AND activity = ? AND semester = ? AND year = ?
        ''', (team, activity, team_semester, team_year))

        team_id = None
        team_row = cursor.fetchone()
        if team_row:
            team_id = team_row[0]

            # create enrollment if not already done
            enrollment_key = (student_id, team_id)
            if enrollment_key not in enrollment_cache:
                cursor.execute('''
                    INSERT INTO enrollments (student_id, team_id)
                    VALUES (?, ?)
                ''', (student_id, team_id))

            conn.commit()
            enrollment_cache.add(enrollment_key)

        # find enrollment_id
        cursor.execute('''
                SELECT enrollment_id FROM enrollments
                WHERE student_id = ? AND team_id = ?
            ''', (student_id, team_id))

        enrollment_row = cursor.fetchone()
        if enrollment_row:
            enrollment_id = enrollment_row[0]

            # create start_datetime by combining date + start_time
            date_part = date_converted.date()


            start_time_part = parse_time_flexible(str(start_time))
            end_time_part = parse_time_flexible(str(end_time))

            start_datetime = datetime.datetime.combine(date_part, start_time_part)
            end_datetime = datetime.datetime.combine(date_part, end_time_part)


            #old datetime code that didnt use the new function which is more flexible
            # create start_datetime by combining date + start_time, might be unneccesary
            # date_part = datetime.datetime.strptime(date, '%d %b %Y').date()  #notorignal -  change back to %Y-%m-%d %H:%M:%S - correct
            # start_time_part = datetime.datetime.strptime(start_time, '%I:%M%p').time()
            # end_time_part = datetime.datetime.strptime(end_time, '%I:%M%p').time()
            # start_datetime = datetime.datetime.combine(date_part, start_time_part)
            # en d_datetime = datetime.datetime.combine(date_part, end_time_part)

            attendance_key = (enrollment_id, start_datetime)
            if attendance_key not in attendance_cache:
                cursor.execute('''
                                INSERT INTO attendance_records (enrollment_id, session_name, session_date, start_time, end_time, staff, attendance_status, is_fixture, has_flags, is_cancelled)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (enrollment_id, session, date, start_datetime, end_datetime, session_staff, attendance, for_fixture, flags, cancelled))

            conn.commit()
            attendance_cache.add(attendance_key)

    #establish which students are enrolled in which teams (enrollment table)

    #capture attendance for each session (attendance_record table)

    conn.close()


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'GET':
        return render_template('upload.html')

    if request.method == 'POST':

        if 'file' not in request.files:
            return jsonify({'error': 'No file part'})

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'})

        if file and file.filename.endswith('.xlsx'):
            # Save a file to a temporary location
            filename = secure_filename(file.filename)   # sanitize filename (disallow special and problematic)
                                                        # characters e.g. ../../file.xlsx)
            file.save(os.path.join('uploads', filename))

            wb = load_workbook(os.path.join('uploads', filename))
            sheet = wb.active

            conn = process_excel_upload.create_connection()
            cursor = conn.cursor()

            # Iterate over the rows (skipping header row)
            cursor.execute('DROP TABLE if exists staging_full_data')
            cursor.execute('DROP TABLE if exists students')
            cursor.execute('DROP TABLE if exists teams')
            cursor.execute('DROP TABLE if exists enrollments')
            cursor.execute('DROP TABLE if exists attendance_records')

            conn.commit()

            process_excel_upload.create_tables()

            for row in sheet.iter_rows(min_row=2, values_only=True):
                (student_id, student_name, year, boarder, house, homeroom, campus, gender, birthdate,
                 secondary, email, team, activity, session, date, start_time, end_time, session_staff, attendance,
                 for_fixture, flags, cancelled) = row

                cursor.execute('''
                        INSERT INTO staging_full_data (
                            student_id, student_name, year, boarder, house, homeroom, campus, gender, birthdate,
                            secondary, email, team, activity, session, date, start_time, end_time, session_staff,
                            attendance, for_fixture, flags, cancelled
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                    student_id, student_name, year, boarder, house, homeroom, campus, gender, birthdate,
                    secondary, email, team, activity, session, date, start_time, end_time, session_staff,
                    attendance, for_fixture, flags, cancelled
                ))

            conn.commit()
            conn.close()

            normalise_and_insert_data()

            return jsonify({"success": "File data added to database"})
        return jsonify({"error": "Invalid file format. Please upload an .xlsx file."})
    return jsonify({"error": "Invalid file format. Please upload an .xlsx file."})



if __name__ == '__main__':
    app.run(debug=True)





















#
#
#
# @app.route('/teacher-year-attendance', methods=['GET', 'POST'])
# def year_attendance():
#     results = []
#     graph_html = ""
#     year_ID = ""
#
#     if request.method == 'POST':
#         # Get the year_ID from the form input
#         year_ID = request.form.get('year_ID', '')
#         results = sport_attendance_by_year(year_ID)
#
#         # Create the attendance graph if we have data
#         if results:
#             # Extract attendance statuses
#             statuses = [record[3] for record in results]  # Attendance status is at index 3
#
#             # Count attendance statuses
#             attendance_count = {"Present": 0, "Explained absence": 0, "Unexplained absence": 0}
#             for status in statuses:
#                 if status in attendance_count:
#                     attendance_count[status] += 1
#
#             # Create Plotly bar chart
#             data = [
#                 go.Bar(
#                     x=list(attendance_count.keys()),
#                     y=list(attendance_count.values()),
#                     marker=dict(color=['green', 'orange', 'red'])
#                 )
#             ]
#
#             # Set graph layout
#             layout = go.Layout(
#                 title=f'Attendance Summary for {year_ID}',
#                 xaxis=dict(title='Attendance Status'),
#                 yaxis=dict(title='Number of Students')
#             )
#
#             # Generate the graph
#             fig = go.Figure(data=data, layout=layout)
#             graph_html = fig.to_html(full_html=False)    # Render the template with results and graph
#     return render_template('daily-attendance-dashboard.html', results=results, graph_html=graph_html, year_ID=year_ID)
#

# @app.route("/student-only-page")
# def student_only_page():
# 	if oidc.user_loggedin:
# 		oidc_profile = session["oidc_auth_profile"]
#
# 		# Teachers can potentially log in through the school's OIDC server
# 		# as well, but we only want students.
# 		if "student_id" not in oidc_profile:
# 			return "SBHS account must be for a student.", 401
#
# 		return f"Hello, {oidc_profile['student_id']}!"
# 	else:
# 		# The argument to this function is what route we want the user to be
# 		# returned to after completing the login. In this case, this page.
# 		return oidc.redirect_to_auth_server("/student-only-page")

#end of copied auth code