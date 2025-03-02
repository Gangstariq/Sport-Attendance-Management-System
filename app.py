from flask import Flask, render_template, request, jsonify
import sqlite3
import os
from werkzeug.utils import secure_filename
import process_excel_upload
from openpyxl import load_workbook
import plotly.graph_objs as go
import plotly.io as pio
import openpyxl
app = Flask(__name__)

app.config["DATABASE_PATH"] = os.path.join(app.root_path, "dataBase", "Chinook_Sqlite.sqlite")

def query_chinook_database(search_term):
    db_path = os.path.join(app.root_path, "dataBase", "Chinook_Sqlite.sqlite")
    query = """
        SELECT Album.Title, Artist.Name
        FROM Album
        JOIN Artist ON Album.ArtistId = Artist.ArtistId
        WHERE Album.Title LIKE ?;
    """
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute(query, (f"%{search_term}%",)) # sql syntax for pattern matching anywhere,
                                                            # passed as a single element tuple

    results = cursor.fetchall()
    connection.close()
    return results

def students_attendance(student_ID):
    db_path = os.path.join(app.root_path, "dataBase", "students.db")
    query = """
        SELECT student_id, activity, attendance, date
        FROM attendance_records
        WHERE student_id LIKE ?
        ORDER BY date DESC;
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
    return render_template('index.html', results=results)

#for my own reference
# record[0] = student_id
# record[1] = activity
# record[2] = attendance (Present, Absent, late?)
# record[3] = date

@app.route('/test_index', methods=['GET', 'POST'])
def test_index():
    results = []
    graph_html = ""
    if request.method == 'POST':
        search_ID = request.form.get('search_ID', '')
        results = students_attendance(search_ID)

    # creates attendence graph if we have data
    if results:
        #geets attendance data by date
        dates = [record[3] for record in results] # date - referenced above "for my own reference"
        statuses = [record[2] for record in results] # attendence

        # makes bar chart data
        attendance_count = {"Present": 0, "Explained absence": 0}
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

    return render_template('test_index.html', results=results, graph_html=graph_html) #converst graph to html graph





@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'GET':
        return render_template('upload.html')

    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({"error": "No file part"})

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"})

        if file and file.filename.endswith('.xlsx'):
            #sav file to temp location
            filename = secure_filename(file.filename)
            file.save(os.path.join('uploads', filename))

            wb = load_workbook(os.path.join('uploads', filename))
            sheet = wb.active
            process_excel_upload.create_tables()
            conn = process_excel_upload.create_connection()
            cursor = conn.cursor()

            #Iterate over the rows (skipping header row)
            for row in sheet.iter_rows(min_row=2, values_only=True):
                (student_id, student_name, year, boarder, house, homeroom, campus, gender, birth_date, secondary, email, team, activity, session, date, start_time, end_time, session_staff, attendance, for_fixture, flags, cancelled) = row
                #inset the student if not already in database
                cursor.execute("""
                    INSERT INTO attendance_records(student_id, activity, attendance, date)
                    VALUES (?,?,?,?)
                """, (student_id, activity, attendance, date))

            conn.commit()
            conn.close()

            return jsonify({"success": "File data added to database"})
        return jsonify({"error": "Invalid file formate. Please upload an .xlsx file."})
    return jsonify({"error": "Invalid file formate. Please upload an .xlsx file."})








if __name__ == '__main__':
    app.run(debug=True)
