# Cloud-Based Smart Campus Emergency Communication and Response System

A beginner-friendly Flask prototype based on the three modules in the project PPT.

## Included modules
1. User Management: registration, login, roles and administrator user list.
2. Emergency Reporting: manual SOS report with emergency type, campus location and description.
3. Communication and Response: incident dashboard, status updates, responder assignment and simulated alert log.

## Important demo limitation
This project runs locally and uses SQLite to make the first demonstration easy. It is **not a production emergency service**. SMS, email, push, IoT/MQTT and GPS are represented as integration points/simulated logs. Do not rely on this prototype for real emergencies. A real deployment needs a secured cloud database, HTTPS, verified accounts, tested notification providers, monitoring, backups and campus-authorized response procedures.

## Run in VS Code
1. Extract the ZIP file.
2. Open VS Code.
3. Select **File > Open Folder** and choose `smart_campus_emergency_system`.
4. Open **Terminal > New Terminal**.
5. Create a virtual environment:
   - Windows: `py -m venv venv`
   - If `py` is unavailable: `python -m venv venv`
6. Activate it:
   - PowerShell: `.\venv\Scripts\Activate.ps1`
   - Command Prompt: `venv\\Scripts\\activate.bat`
7. Install packages: `python -m pip install -r requirements.txt`
8. Run: `python app.py`
9. Open the address shown in the terminal, usually `http://127.0.0.1:5000`.

## Demo accounts
- Administrator: `admin@campus.demo` / `Admin@123`
- Student: `student@campus.demo` / `Demo@123`
- Faculty: `faculty@campus.demo` / `Demo@123`
- Security: `security@campus.demo` / `Demo@123`

Change demo passwords and the Flask secret key before any deployment.

## Architecture mapping
Browser UI (HTML/CSS/JS) -> Flask routes/API layer -> SQLite demo database.
For the PPT cloud version, replace SQLite with MySQL/Firestore and deploy Flask on AWS/Azure/Firebase-compatible hosting. Connect Twilio/SMTP/FCM for real notifications, MQTT for authorized sensor gateways, and a Maps/GPS provider for location display.
