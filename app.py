from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta

app = Flask(__name__)

# SECRET_KEY من متغير البيئة
secret = os.environ.get('SECRET_KEY')
if not secret:
    raise RuntimeError("يرجى تعيين متغير البيئة SECRET_KEY قبل تشغيل التطبيق.")
app.config['SECRET_KEY'] = secret
app.permanent_session_lifetime = timedelta(hours=4)

# إعداد قاعدة البيانات Supabase/Postgres
db_config = {
    'host': os.environ.get('DB_HOST', 'db.spqewghstdwgiwpxtfar.supabase.co'),
    'port': int(os.environ.get('DB_PORT', 5432)),
    'database': os.environ.get('DB_NAME', 'postgres'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', '2jpL3a%rB77/@k7'),
    'sslmode': 'require'  # مهم لأن SSL مفعل في Supabase
}

# دالة اتصال قاعدة البيانات
def get_db_connection():
    return psycopg2.connect(**db_config, cursor_factory=RealDictCursor)

# صفحة تسجيل الدخول
@app.route('/', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        password = request.form.get('password', '')
        if not name or not password:
            return render_template('login.html', error="يرجى إدخال الاسم وكلمة المرور.")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, password FROM students WHERE name=%s", (name,))
            student = cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

        if student and check_password_hash(student['password'], password):
            session.permanent = True
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

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT subject, grade FROM grades WHERE student_id=%s", (student_id,))
        grades = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return render_template('dashboard.html', grades=grades)

# API لتسجيل الدخول
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    password = data.get('password', '')
    if not name or not password:
        return jsonify({"success": False, "message": "الاسم وكلمة المرور مطلوبان"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, password FROM students WHERE name=%s", (name,))
        student = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    if student and check_password_hash(student['password'], password):
        return jsonify({"success": True, "student_id": student['id']})
    else:
        return jsonify({"success": False, "message": "اسم أو كلمة مرور خاطئة"}), 401

# API لجلب الدرجات
@app.route('/api/grades/<int:student_id>', methods=['GET'])
def get_grades(student_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT subject, grade FROM grades WHERE student_id=%s", (student_id,))
        grades = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
    return jsonify({"grades": grades})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
