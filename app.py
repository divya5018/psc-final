from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
import psycopg2

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = 'your_secret_key'

# Database connection
conn = psycopg2.connect(
    dbname='postgres',
    user='postgres',
    password='123',
    host='localhost'
)
cursor = conn.cursor()

# Routes

# Index page
@app.route('/')
def index():
    return render_template('index.html')

# Teacher login
# Teacher login
@app.route('/login_teacher', methods=['GET', 'POST'])
def login_teacher():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor.execute('SELECT * FROM users WHERE username = %s AND role = %s', (username, 'teacher'))
        user = cursor.fetchone()
        if user and user[2] == password:  # Direct comparison without hashing
            session['user_id'] = user[0]
            session['role'] = user[3]
            flash('Logged in successfully', 'success')
            return redirect(url_for('teacher_dashboard'))  # Redirect to teacher dashboard
        else:
            flash('Invalid username or password', 'error')
    return render_template('login_teacher.html')

# Student login
@app.route('/login_student', methods=['GET', 'POST'])
def login_student():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor.execute('SELECT * FROM users WHERE username = %s AND role = %s', (username, 'student'))
        user = cursor.fetchone()
        if user and user[2] == password:  # Direct comparison without hashing
            session['user_id'] = user[0]
            session['role'] = user[3]
            flash('Logged in successfully', 'success')
            return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login_student.html')

# Teacher dashboard
@app.route('/teacher/dashboard')
def teacher_dashboard():
    if 'user_id' in session and session['role'] == 'teacher':
        # Fetch the teacher's name from the database based on the session user_id
        cursor.execute('SELECT username FROM users WHERE id = %s', (session['user_id'],))
        user = cursor.fetchone()
        if user:
            username = user[0]
            # Logic to fetch and display teacher dashboard data
            # Assuming you fetch the courses from the database
            cursor.execute('SELECT title, description FROM courses WHERE teacher_id = %s', (session['user_id'],))
            courses = cursor.fetchall()
            return render_template('teacher_dashboard.html', username=username, courses=courses)
        else:
            flash('Teacher not found', 'error')
            return redirect(url_for('login_teacher'))
    else:
        return redirect(url_for('login_teacher'))

# Student dashboard
@app.route('/student/dashboard')
def student_dashboard():
    if 'user_id' in session and session['role'] == 'student':
        # Fetch all courses from the database
        cursor.execute('SELECT title, description FROM courses')
        courses = cursor.fetchall()
        return render_template('student_dashboard.html', courses=courses)
    else:
        return redirect(url_for('login_student'))

# Course creation form
@app.route('/create_course_form', methods=['GET'])
def create_course_form():
    if 'user_id' in session and session['role'] == 'teacher':
        return render_template('create_course_form.html')
    else:
        flash('You need to log in as a teacher to access this page.', 'error')
        return redirect(url_for('login_teacher'))

# Course creation
@app.route('/create_course', methods=['POST'])
def create_course():
    if 'user_id' in session and session['role'] == 'teacher':
        if request.method == 'POST':
            title = request.form['title']
            description = request.form['description']
            teacher_id = session['user_id']
            # Insert course data into the database
            cursor.execute('INSERT INTO courses (title, description, teacher_id) VALUES (%s, %s, %s)', (title, description, teacher_id))
            conn.commit()
            flash('Course created successfully', 'success')
            return redirect(url_for('teacher_dashboard'))
    else:
        flash('You need to log in as a teacher to perform this action.', 'error')
        return redirect(url_for('login_teacher'))

# Enroll in a course
@app.route('/enroll_course', methods=['POST'])
def enroll_course():
    if 'user_id' in session and session['role'] == 'student':
        if request.method == 'POST':
            course_id = request.form['course_id']
            student_id = session['user_id']
            # Check if the student is already enrolled in the course
            cursor.execute('SELECT * FROM enrolled_courses WHERE student_id = %s AND course_id = %s', (student_id, course_id))
            enrolled_course = cursor.fetchone()
            if enrolled_course:
                flash('You are already enrolled in this course.', 'error')
            else:
                # Enroll the student in the course
                cursor.execute('INSERT INTO enrolled_courses (student_id, course_id) VALUES (%s, %s)', (student_id, course_id))
                conn.commit()
                flash('Enrolled in course successfully', 'success')
        return redirect(url_for('student_dashboard'))
    else:
        flash('You need to log in as a student to perform this action.', 'error')
        return redirect(url_for('login_student'))

# Drop a course
@app.route('/drop_course', methods=['POST'])
def drop_course():
    if 'user_id' in session and session['role'] == 'student':
        if request.method == 'POST':
            course_id = request.form['course_id']
            student_id = session['user_id']
            # Remove the student from the enrolled course
            cursor.execute('DELETE FROM enrolled_courses WHERE student_id = %s AND course_id = %s', (student_id, course_id))
            conn.commit()
            flash('Course dropped successfully', 'success')
        return redirect(url_for('student_dashboard'))
    else:
        flash('You need to log in as a student to perform this action.', 'error')
        return redirect(url_for('login_student'))

# Course discussion page
@app.route('/course/discussion/<int:course_id>')
def course_discussion(course_id):
    if 'user_id' in session:  # Ensure user is logged in
        # Fetch course discussions from the database based on the course_id
        cursor.execute('SELECT * FROM discussions WHERE course_id = %s', (course_id,))
        discussions = cursor.fetchall()
        return render_template('course_discussion.html', discussions=discussions)
    else:
        flash('You need to log in to access this page.', 'error')
        return redirect(url_for('login'))

# Create new discussion thread
@app.route('/course/discussion/<int:course_id>/new_thread', methods=['GET', 'POST'])
def new_thread(course_id):
    if 'user_id' in session:  # Ensure user is logged in
        if request.method == 'POST':
            title = request.form['title']
            initial_post = request.form['initial_post']
            # Insert the new thread into the database
            cursor.execute('INSERT INTO discussions (course_id, title, initial_post) VALUES (%s, %s, %s)', (course_id, title, initial_post))
            conn.commit()
            flash('New thread created successfully', 'success')
            return redirect(url_for('course_discussion', course_id=course_id))
        else:
            return render_template('new_thread.html')
    else:
        flash('You need to log in to access this page.', 'error')
        return redirect(url_for('login'))

# Reply to a discussion thread
@app.route('/course/discussion/<int:course_id>/thread/<int:thread_id>/reply', methods=['POST'])
def reply_to_thread(course_id, thread_id):
    if 'user_id' in session:  # Ensure user is logged in
        if request.method == 'POST':
            reply_content = request.form['reply_content']
            # Insert the reply into the database
            cursor.execute('INSERT INTO replies (thread_id, user_id, content) VALUES (%s, %s, %s)', (thread_id, session['user_id'], reply_content))
            conn.commit()
            flash('Reply added successfully', 'success')
            return redirect(url_for('view_thread', course_id=course_id, thread_id=thread_id))
    else:
        flash('You need to log in to access this page.', 'error')
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
