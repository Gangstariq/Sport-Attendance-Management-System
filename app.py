from flask import Flask, render_template, request, jsonify
import sqlite3
import os
from werkzeug.utils import secure_filename
import process_excel_upload
from openpyxl import load_workbook
import plotly.graph_objs as go
import plotly.io as pio
import json
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

@app.route('/', methods=['GET', 'POST'])
def home():
    results = []
    if request.method == 'POST':
        search_term = request.form.get('search_term', '')
        results = query_chinook_database(search_term)
    return render_template('index.html', results=results)


@app.route('/get_attendance_data')
def get_attendance_data():
    conn = sqlite3.connect(app.config["students.db"])
    cursor = conn.cursor()

    cursor.execute("""
        SELECT date, COUNT(*) as attendance_count 
        FROM attendance_records 
        WHERE attendance = 'Present' 
        GROUP BY date 
        ORDER BY date
    """)

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
