import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "dataBase", "students.db")

def daily_attendance_summary(year_ID):
    #basically SUM counts how many were present/abscent that day so adds up all the '1' values
    #Case WHEN is like an if condition so if it was 'present' then set the value to 1 (present) or else o (not present)
    #AS present_count just sets it to like a variable ot make it easier ot reference and renames it
    #CAST converts the date into an integer so its like ordered correctly
    query = """
        SELECT DISTINCT date, 
               SUM(CASE WHEN attendance = 'Present' THEN 1 ELSE 0 END) AS present_count,
               SUM(CASE WHEN attendance = 'Explained absence' THEN 1 ELSE 0 END) AS explained_absence_count,
               SUM(CASE WHEN attendance = 'Unexplained absence' THEN 1 ELSE 0 END) AS unexplained_absence_count
        FROM attendance_records
        WHERE year = ?
        GROUP BY date
        ORDER BY CAST(date AS integer) ASC; 
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(query, (str(year_ID),))
    results = cursor.fetchall()
    connection.close()
    return results
