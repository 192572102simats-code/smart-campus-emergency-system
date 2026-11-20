from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from pathlib import Path
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change-this-demo-secret"
DB = Path(__file__).with_name("campus_emergency.db")

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            department TEXT DEFAULT '',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reporter_id INTEGER,
            reporter_name TEXT NOT NULL,
            emergency_type TEXT NOT NULL,
            location TEXT NOT NULL,
            description TEXT,
            priority TEXT NOT NULL DEFAULT 'High',
            status TEXT NOT NULL DEFAULT 'Pending',
            assigned_team TEXT DEFAULT 'Not assigned',
            created_at TEXT NOT NULL,
            FOREIGN KEY(reporter_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS alert_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id INTEGER NOT NULL,
            channel TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """)
        admin = con.execute("SELECT id FROM users WHERE email=?", ("admin@campus.demo",)).fetchone()
        if not admin:
            con.execute(
                "INSERT INTO users(name,email,password,role,department,created_at) VALUES(?,?,?,?,?,?)",
                ("Campus Administrator", "admin@campus.demo",
                 generate_password_hash("Admin@123"), "Administrator", "Administration",
                 datetime.now().strftime("%Y-%m-%d %H:%M"))
            )
        count = con.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
        if count == 1:
            demo_users = [
                ("Student Demo", "student@campus.demo", "Student", "Computer Science"),
                ("Faculty Demo", "faculty@campus.demo", "Faculty", "Electronics"),
                ("Security Demo", "security@campus.demo", "Security", "Campus Security"),
            ]
            for name, email, role, dept in demo_users:
                con.execute(
                    "INSERT INTO users(name,email,password,role,department,created_at) VALUES(?,?,?,?,?,?)",
                    (name, email, generate_password_hash("Demo@123"), role, dept,
                     datetime.now().strftime("%Y-%m-%d %H:%M"))
                )

def current_user():
    if "user_id" not in session:
        return None
    with db() as con:
        return con.execute("SELECT id,name,email,role,department FROM users WHERE id=?",
                           (session["user_id"],)).fetchone()

@app.context_processor
def inject_user():
    return {"logged_user": current_user()}

@app.route("/")
def home():
    if not current_user():
        return redirect(url_for("login"))
    return redirect(url_for("dashboard"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with db() as con:
            user = con.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            flash("Login successful.", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "Student")
        department = request.form.get("department", "").strip()
        if not name or not email or len(password) < 6:
            flash("Enter all required details. Password must contain at least 6 characters.", "error")
        else:
            try:
                with db() as con:
                    con.execute(
                        "INSERT INTO users(name,email,password,role,department,created_at) VALUES(?,?,?,?,?,?)",
                        (name, email, generate_password_hash(password), role, department,
                         datetime.now().strftime("%Y-%m-%d %H:%M"))
                    )
                flash("Registration complete. Please log in.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("This email is already registered.", "error")
    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    with db() as con:
        total = con.execute("SELECT COUNT(*) n FROM incidents").fetchone()["n"]
        active = con.execute("SELECT COUNT(*) n FROM incidents WHERE status != 'Resolved'").fetchone()["n"]
        resolved = con.execute("SELECT COUNT(*) n FROM incidents WHERE status='Resolved'").fetchone()["n"]
        users_count = con.execute("SELECT COUNT(*) n FROM users").fetchone()["n"]
        incidents = con.execute("SELECT * FROM incidents ORDER BY id DESC LIMIT 8").fetchall()
    return render_template("dashboard.html", total=total, active=active, resolved=resolved,
                           users_count=users_count, incidents=incidents)

@app.route("/report", methods=["GET", "POST"])
def report():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    if request.method == "POST":
        emergency_type = request.form.get("emergency_type", "")
        location = request.form.get("location", "").strip()
        description = request.form.get("description", "").strip()
        priority = request.form.get("priority", "High")
        if not emergency_type or not location:
            flash("Select an emergency type and enter the location.", "error")
        else:
            with db() as con:
                cur = con.execute(
                    """INSERT INTO incidents(reporter_id,reporter_name,emergency_type,location,
                    description,priority,status,assigned_team,created_at)
                    VALUES(?,?,?,?,?,?, 'Pending','Not assigned',?)""",
                    (user["id"], user["name"], emergency_type, location, description, priority,
                     datetime.now().strftime("%Y-%m-%d %H:%M"))
                )
                incident_id = cur.lastrowid
                # Demo-only alert log. No real SMS/email/push message is sent.
                for channel in ("Dashboard", "SMS (simulation)", "Email (simulation)", "Push (simulation)"):
                    con.execute(
                        "INSERT INTO alert_logs(incident_id,channel,message,created_at) VALUES(?,?,?,?)",
                        (incident_id, channel,
                         f"New {emergency_type} incident reported at {location}",
                         datetime.now().strftime("%Y-%m-%d %H:%M"))
                    )
            flash(f"Emergency report #{incident_id} submitted. Demo alert logs were created.", "success")
            return redirect(url_for("incidents"))
    return render_template("report.html")

@app.route("/incidents")
def incidents():
    if not current_user():
        return redirect(url_for("login"))
    with db() as con:
        rows = con.execute("SELECT * FROM incidents ORDER BY id DESC").fetchall()
    return render_template("incidents.html", incidents=rows)

@app.route("/incident/<int:incident_id>/update", methods=["POST"])
def update_incident(incident_id):
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    if user["role"] not in ("Administrator", "Security", "Faculty"):
        flash("Only response staff can update incident status.", "error")
        return redirect(url_for("incidents"))
    status = request.form.get("status", "Pending")
    team = request.form.get("assigned_team", "Not assigned")
    if status not in ("Pending", "Verified", "Responding", "Resolved"):
        status = "Pending"
    with db() as con:
        con.execute("UPDATE incidents SET status=?, assigned_team=? WHERE id=?",
                    (status, team, incident_id))
    flash(f"Incident #{incident_id} updated.", "success")
    return redirect(url_for("incidents"))

@app.route("/users")
def users():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    if user["role"] != "Administrator":
        flash("Only administrators can view user management.", "error")
        return redirect(url_for("dashboard"))
    with db() as con:
        rows = con.execute("SELECT id,name,email,role,department,created_at FROM users ORDER BY id").fetchall()
    return render_template("users.html", users=rows)

@app.route("/alerts")
def alerts():
    if not current_user():
        return redirect(url_for("login"))
    with db() as con:
        rows = con.execute("""SELECT alert_logs.*, incidents.emergency_type, incidents.location
                              FROM alert_logs JOIN incidents ON incidents.id=alert_logs.incident_id
                              ORDER BY alert_logs.id DESC""").fetchall()
    return render_template("alerts.html", alerts=rows)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
