import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, session
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



@app.route('/')
def home():
    return render_template('home.html')


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