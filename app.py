from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
import os

# -------------------------
# قراءة متغيرات البيئة
# -------------------------
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = int(os.environ.get("DB_PORT", 5432))
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
SECRET_KEY = os.environ.get("SECRET_KEY")

if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, SECRET_KEY]):
    raise RuntimeError("يجب تعيين جميع متغيرات البيئة: DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, SECRET_KEY")

# -------------------------
# إعداد Flask
# -------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.permanent_session_lifetime = timedelta(hours=4)

db_config = {
    'host': DB_HOST,
    'port': DB_PORT,
    'database': DB_NAME,
    'user': DB_USER,
    'password': DB_PASSWORD,
    'sslmode': 'require'
}

# -------------------------
# دالة اتصال قاعدة البيانات
# -------------------------
def get_db_connection():
    return psycopg2.connect(**db_config, cursor_factory=RealDictCursor)

# -------------------------
# باقي الكود يبقى كما هو
# صفحة تسجيل الدخول، لوحة الدرجات، APIs
# -------------------------
@app.route('/', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        password = request.form.get('password', '')

        if not name or not password:
            return render_template('login.html', error="يرجى إدخال الاسم وكلمة المرور.")

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT id, password FROM students WHERE name=%s", (name,))
                    student = cursor.fetchone()
        except Exception as e:
            return render_template('login.html', error=f"خطأ في الاتصال بقاعدة البيانات: {e}")

        if student and check_password_hash(student['password'], password):
            session.permanent = True
            session['student_id'] = student['id']
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="اسم أو كلمة مرور خاطئة")

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    student_id = session.get('student_id')
    if not student_id:
        return redirect(url_for('login_page'))

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT subject, grade FROM grades WHERE student_id=%s", (student_id,))
                grades = cursor.fetchall()
    except Exception as e:
        return f"خطأ في جلب البيانات: {e}"

    return render_template('dashboard.html', grades=grades)

# -------------------------
# تشغيل التطبيق
# -------------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

