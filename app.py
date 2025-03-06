from flask import Flask, render_template, request, jsonify, session
import sqlite3
import os
from werkzeug.utils import secure_filename
from openpyxl import load_workbook
import plotly.graph_objs as go
import plotly.io as pio
import openpyxl
from flask_oidc import OpenIDConnect


#imports of other python functions:
import process_excel_upload
import attendance_queries
from average_attendance_per_activity import activity_attendance



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


#TEACHER ROUTING FUNCTIONS (ALL LINK TO A .PY FUNCTION)
@app.route('/daily-attendance-dashboard', methods=['GET', 'POST'])
def daily_attendance_dashboard():
    results = []
    year_ID = ""

    if request.method == 'POST':
        year_ID = request.form.get('year_ID', '')
        results = attendance_queries.daily_attendance_summary(year_ID)  # Call function from external file

    return render_template('Teacher/daily-attendance-dashboard.html', results=results, year_ID=year_ID)


@app.route('/daily-attendance-dashboard-graph', methods=['GET', 'POST'])
def daily_attendance_graph():
    results = []
    graph_html = ""
    year_ID = ""

    if request.method == 'POST':
        # Get the year_ID from the form input
        year_ID = request.form.get('year_ID', '')
        results = attendance_queries.daily_attendance_summary(year_ID)  # Fetch data from DB

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

    return render_template('Teacher/average-attendance-per-activity.html', results=results, graph_html=graph_html, year_ID=year_ID)













def sport_attendance_by_year(year_ID):
    db_path = os.path.join(app.root_path, "dataBase", "students.db")
    query = f"""
            SELECT DISTINCT student_id, year, activity, attendance, date
            FROM attendance_records
            WHERE year = ?;
        """
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute(query, (str(year_ID),))  # Ensure year_ID is a string
    results = cursor.fetchall()

    connection.close()  # Always close the database connection
    return results








@app.route("/student-only-page")
def student_only_page():
	if oidc.user_loggedin:
		oidc_profile = session["oidc_auth_profile"]

		# Teachers can potentially log in through the school's OIDC server
		# as well, but we only want students.
		if "student_id" not in oidc_profile:
			return "SBHS account must be for a student.", 401

		return f"Hello, {oidc_profile['student_id']}!"
	else:
		# The argument to this function is what route we want the user to be
		# returned to after completing the login. In this case, this page.
		return oidc.redirect_to_auth_server("/student-only-page")

#end of copied auth code


def students_attendance(student_ID):
    db_path = os.path.join(app.root_path, "dataBase", "students.db")
    query = """
        SELECT DISTINCT student_id, activity, attendance, date
        FROM attendance_records
        WHERE student_id LIKE ?;
    """
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute(query, (f"%{student_ID}%",)) # sql syntax for pattern matching anywhere,
                                                            # passed as a single element tuple

    results = cursor.fetchall()
    connection.close()
    return results


@app.route('/', methods=['GET', 'POST'])
def home():
    results = []
    if request.method == 'POST':
        search_term = request.form.get('search_term', '')
        results = query_chinook_database(search_term)
    return render_template('teacher-home.html', results=results)



@app.route('/individual_student_attendance', methods=['GET', 'POST'])
def individual_student_attendance():
    results = []
    graph_html = ""
    if request.method == 'POST':
        search_ID = request.form.get('search_ID', '')
        results = students_attendance(search_ID)

    # for my own reference
    # record[0] = student_id
    # record[1] = activity
    # record[2] = attendance (Present, Absent, late?)
    # record[3] = date

    # creates attendence graph if we have data
    if results:
        #gets attendance data by date
        dates = [record[3] for record in results] # date - referenced above "for my own reference"
        statuses = [record[2] for record in results] # attendence

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

    return render_template('Student access/individual_student_attendance.html', results=results, graph_html=graph_html) #converst graph to html graph




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

            process_excel_upload.create_tables()

            conn = process_excel_upload.create_connection()
            cursor = conn.cursor()

            # Iterate over the rows (skipping header row)

            for row in sheet.iter_rows(min_row=2, values_only=True):
                (student_id, student_name, year, boarder, house, homeroom, campus, gender, birthdate,
                 secondary, email, team, activity, session, date, start_time, end_time, session_staff, attendance,
                 for_fixture, flags, cancelled) = row



                # Insert the attendance record

                cursor.execute('''
                    INSERT INTO attendance_records (student_id, activity, attendance, date, year)
                    VALUES (?, ?, ?, ?, ?)
                ''', (student_id, activity, attendance, date, year))



            conn.commit()
            conn.close()


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

