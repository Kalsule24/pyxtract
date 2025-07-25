import os, re
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, session
from werkzeug.utils import secure_filename
import mimetypes

from utils.extract_image import extract_text_from_image
from utils.extract_pdf import extract_text_from_pdf
from utils.extract_docx import extract_text_from_docx
from utils.save_to_db import save_extraction
from utils.exporter import export_as_txt, export_as_pdf, export_as_docx

from flask_mysqldb import MySQL
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

# ✅ Initialize the app only ONCE
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_key")  # Needed for sessions and flash messages

# ✅ MySQL configuration
app.config['MYSQL_HOST'] = DB_HOST
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = DB_USER
app.config['MYSQL_PASSWORD'] = DB_PASSWORD
app.config['MYSQL_DB'] = DB_NAME
#app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# ✅ Initialize MySQL
mysql = MySQL(app)

# ✅ Upload folder config
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

last_uploaded_id = None

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/start-extract', methods=['GET', 'POST'])
def index():
    global last_uploaded_id
    extracted_text = ""
    file_info = {}

    if request.method == 'POST' and 'file' in request.files:
        uploaded_file = request.files['file']
        if uploaded_file.filename != '':
            filename = secure_filename(uploaded_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            uploaded_file.save(filepath)

            filetype = mimetypes.guess_type(filepath)[0]
            if filetype:
                if filetype.startswith('image'):
                    extracted_text = extract_text_from_image(filepath)
                    filetype = 'image'
                elif filetype == 'application/pdf':
                    extracted_text = extract_text_from_pdf(filepath)
                    filetype = 'pdf'
                elif filetype == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                    extracted_text = extract_text_from_docx(filepath)
                    filetype = 'docx'
                else:
                    extracted_text = "❌ Unsupported file type."
                    filetype = 'unknown'

                if filetype in ['image', 'pdf', 'docx']:
                    last_uploaded_id = save_extraction(filename, filetype, extracted_text)
                    print("Inserted ID (last_uploaded_id):", last_uploaded_id)

                file_info = {'filename': filename, 'filetype': filetype}

    return render_template('index.html', text=extracted_text, file=file_info)

@app.route('/history', methods=['GET', 'POST'])
def history():
    cur = mysql.connection.cursor()
    query = "SELECT * FROM extracted_files ORDER BY extracted_at DESC"

    if request.method == "POST":
        search_term = request.form.get("search", "")
        query = (
            "SELECT * FROM extracted_files "
            "WHERE filename LIKE %s OR filetype LIKE %s "
            "ORDER BY extracted_at DESC"
        )
        cur.execute(query, (f"%{search_term}%", f"%{search_term}%"))
    else:
        cur.execute(query)

    rows = cur.fetchall()
    cur.close()
    return render_template("history.html", records=rows)

@app.route('/view/<int:id>', methods=['GET', 'POST'])
def view_text(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM extracted_files WHERE id = %s", (id,))
    record = cur.fetchone()

    if not record:
        cur.close()
        return "❌ Record not found", 404

    saved = False
    search_query = ''
    highlighted_text = record['extracted_text']

    if request.method == 'POST':
        action = request.form.get("action")

        if action == "save":
            new_text = request.form.get("edited_text", "")
            cur.execute("UPDATE extracted_files SET extracted_text = %s WHERE id = %s", (new_text, id))
            mysql.connection.commit()
            record['extracted_text'] = new_text
            saved = True
            flash("✔️ Saved successfully!", "success")

        elif action == "search":
            search_query = request.form.get("search_term", "").strip()
            highlighted_text = re.sub(
                re.escape(search_query),
                lambda m: f"<mark>{m.group(0)}</mark>",
                record['extracted_text'],
                flags=re.IGNORECASE
            )

        elif action == "export":
            format = request.form.get("format")
            filename = os.path.splitext(record["filename"])[0]

            if format == "txt":
                export_path = export_as_txt(record["extracted_text"], filename)
            elif format == "pdf":
                export_path = export_as_pdf(record["extracted_text"], filename)
            elif format == "docx":
                export_path = export_as_docx(record["extracted_text"], filename)
            else:
                export_path = None

            cur.close()
            if export_path:
                return redirect(f"/download/{os.path.basename(export_path)}")

    cur.close()
    return render_template("view_text.html", record=record, highlighted_text=highlighted_text, search_term=search_query, saved=saved)

@app.route('/view_latest')
def view_latest():
    global last_uploaded_id
    if last_uploaded_id is None:
        return "❌ No recent extraction found", 404
    return redirect(url_for('view_text', id=last_uploaded_id))

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory("exports", filename, as_attachment=True)

@app.route('/test_mysql')
def test_mysql():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT DATABASE()")
        result = cur.fetchone()
        return f"Connected to DB: {result['DATABASE()']}"
    except Exception as e:
        return f"Error: {str(e)}"


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM signup WHERE username = %s", (username,))
        user = cur.fetchone()

        if not user:
            flash("❌ User not found. Please sign up first.", "danger")
            return redirect(url_for('signup'))

        if user['password'] == password:
            session['user'] = username
            flash("✅ Logged in successfully!", "success")
            return redirect(url_for('index'))
        else:
            flash("❌ Incorrect password. Try again.", "danger")

        cur.close()
    return render_template("login.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("❗ Passwords do not match.", "danger")
            return redirect(url_for('signup'))

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM signup WHERE username = %s", (username,))
        existing_user = cur.fetchone()

        if existing_user:
            flash("❗ Username already exists. Choose another.", "warning")
            cur.close()
            return redirect(url_for('signup'))

        cur.execute("INSERT INTO signup (username, email, password) VALUES (%s, %s, %s)",
                    (username, email, password))
        mysql.connection.commit()
        cur.close()

        flash("✅ Account created successfully! Please login.", "success")
        return redirect(url_for('login'))

    return render_template("signup.html")

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        name = request.form.get("name")
        message = request.form.get("message")
        flash("Thank you for your feedback!", "success")
        return redirect(url_for('home'))
    return render_template("feedback.html")




if __name__ == '__main__':
    app.run(debug=True)
