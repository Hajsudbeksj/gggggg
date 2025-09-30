from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import mysql.connector
import os
import sys

app = Flask(__name__)  # ← تم تصحيح هذا

# قراءة SECRET_KEY من متغير البيئة
secret = os.environ.get('SECRET_KEY')
if not secret:
    sys.exit("ERROR: يرجى تعيين متغير البيئة SECRET_KEY قبل تشغيل التطبيق.")
app.secret_key = secret

# إعداد قاعدة البيانات
db_config = {
    'host': os.environ.get('DB_HOST', 'sql.freedb.tech'),
    'user': os.environ.get('DB_USER', 'freedb_Jsskjsbsd'),
    'password': os.environ.get('DB_PASSWORD', 'fzAnf26Wq?%n@jd'),
    'database': os.environ.get('DB_NAME', 'freedb_Student1 zjsjsn')
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# صفحة تسجيل الدخول
@app.route('/', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM students WHERE name=%s AND password=%s", (name, password))
        student = cursor.fetchone()
        conn.close()
        if student:
            session['student_id'] = student['id']
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="اسم أو كلمة مرور خاطئة")
    return render_template('login.html')

# لوحة الدرجات
@app.route('/dashboard')
def dashboard():
    student_id = session.get('student_id')
    if not student_id:
        return redirect(url_for('login_page'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT subject, grade FROM grades WHERE student_id=%s", (student_id,))
    grades = cursor.fetchall()
    conn.close()
    return render_template('dashboard.html', grades=grades)

# API لتسجيل الدخول
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    name = data.get('name')
    password = data.get('password')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students WHERE name=%s AND password=%s", (name, password))
    student = cursor.fetchone()
    conn.close()
    if student:
        return jsonify({"success": True, "student_id": student['id']})
    else:
        return jsonify({"success": False, "message": "اسم أو كلمة مرور خاطئة"})

# API لجلب الدرجات
@app.route('/api/grades/<int:student_id>', methods=['GET'])
def get_grades(student_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT subject, grade FROM grades WHERE student_id=%s", (student_id,))
    grades = cursor.fetchall()
    conn.close()
    return jsonify({"grades": grades})

if __name__ == '__main__':  # ← تم تصحيح هذا
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
