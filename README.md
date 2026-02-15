SBHS Sports Attendance Management System
A web app I built to help teachers and students track sports attendance at Sydney Boys High School as apart of my HSC major work.
What it does
For Teachers:

Upload attendance data from Excel files
- View daily attendance trends by year group
- Check which sports have the best/worst attendance
- Find students who need help (low attendance alerts)
- Track attendance streaks to motivate students
- Manage individual teams and see player stats

For Students:

- See your own attendance stats
- Track your attendance streaks
- View your recent sessions

Tech Stack

- Backend: Python, Flask, SQLite
- Frontend: HTML, CSS, Bootstrap 5, Plotly charts
- Auth: OpenID Connect (SBHS AUTH)

Database
- Used a normalized relational database with 4 tables:

1. students - student info
2. teams - sport/activity teams
3. enrollments - links students to teams
4. attendance_records - session attendance data
