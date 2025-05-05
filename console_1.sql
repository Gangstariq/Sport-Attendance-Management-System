SELECT DISTINCT students.student_id, teams.team_name, activity, attendance_status, session_date
FROM students, attendance_records, enrollments, teams
WHERE students.student_id = enrollments.student_id
  AND enrollments.team_id = teams.team_id
  AND enrollments.enrollment_id = attendance_records.enrollment_id
  AND students.student_id LIKE ?
ORDER BY students.student_id, session_date, team_name, activity