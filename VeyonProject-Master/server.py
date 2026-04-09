import os
import sqlite3
from flask import Flask, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

online_students = {}
TIMEOUT_SECONDS = 45 

# --- NEW: DATABASE INITIALIZATION ---
def init_db():
    """ Creates a local SQL database and fills it with schedule data """
    conn = sqlite3.connect('university.db')
    c = conn.cursor()
    
    # Create the Schedule Table
    c.execute('''CREATE TABLE IF NOT EXISTS schedule
                 (doctor_id TEXT, doctor_name TEXT, class_name TEXT, day TEXT, start_time TEXT, end_time TEXT)''')
    
    # Clear old data so we start fresh every time for the prototype
    c.execute('DELETE FROM schedule')
    
    # INSERT DEMO DATA
    # Format: 24-hour time. 
    # Doctor 1001 is teaching on Wednesday afternoon (Matches your current time!)
    c.execute("INSERT INTO schedule VALUES ('1001', 'Dr. Ahmed', 'SWE-301: Software Engineering (Lab A)', 'Wednesday', '13:00', '18:00')")
    c.execute("INSERT INTO schedule VALUES ('1001', 'Dr. Ahmed', 'CS-202: Networking (Main Lab)', 'Thursday', '08:00', '12:00')")
    
    # Doctor 2002 is teaching something else
    c.execute("INSERT INTO schedule VALUES ('2002', 'Dr. Khalid', 'CS-599: Graduation Project Work', 'Wednesday', '08:00', '12:00')")
    
    conn.commit()
    conn.close()
    print("[SQL] Database Initialized and Populated.")

# Initialize the DB right when the server script runs
init_db()

@app.route('/')
def home():
    return "Central Server is Running!"

@app.route('/api/heartbeat', methods=['POST'])
def receive_heartbeat():
    data = request.json
    machine_id = data.get('machine_id')
    ip = data.get('ip')
    
    if machine_id and ip:
        online_students[machine_id] = {
            "ip": ip,
            "last_seen": datetime.now()
        }
        return jsonify({"status": "ok"}), 200
    return jsonify({"error": "missing data"}), 400

@app.route('/api/list_students', methods=['GET'])
def list_students():
    cutoff_time = datetime.now() - timedelta(seconds=TIMEOUT_SECONDS)
    
    to_remove = []
    for name, info in online_students.items():
        if info['last_seen'] < cutoff_time:
            to_remove.append(name)
            
    for name in to_remove:
        del online_students[name]

    student_list = []
    for name, info in online_students.items():
        student_list.append({"name": name, "ip": info['ip'], "mac": ""})
        
    return jsonify(student_list)

@app.route('/api/get_key', methods=['GET'])
def get_key():
    key_path = 'teacher_private_key.pem'
    if not os.path.exists(key_path):
        return jsonify({"status": "error", "message": "Key file not found."}), 404
    try:
        with open(key_path, 'r') as f:
            key_data = f.read()
        return jsonify({"status": "success", "key": key_data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- UPDATED: SMART SQL ENDPOINT ---
@app.route('/api/get_classes', methods=['GET'])
def get_classes():
    """ Returns classes based on Doctor ID, Current Day, and Current Time """
    doctor_id = request.args.get('doctor_id')
    
    if not doctor_id:
        return jsonify({"status": "error", "message": "Missing Doctor ID"}), 400

    # Get the real current day and time
    current_day = datetime.now().strftime("%A") # e.g., "Wednesday"
    current_time = datetime.now().strftime("%H:%M") # e.g., "15:30"
    
    print(f"[SQL Query] Fetching schedule for ID: {doctor_id} at {current_day} {current_time}")

    conn = sqlite3.connect('university.db')
    c = conn.cursor()
    
    # Query the database
    c.execute('''SELECT class_name FROM schedule 
                 WHERE doctor_id = ? AND day = ? AND start_time <= ? AND end_time >= ?''', 
              (doctor_id, current_day, current_time, current_time))
    
    results = c.fetchall()
    conn.close()
    
    # Convert SQL results into a simple Python list
    classes = [row[0] for row in results]
    
    if not classes:
        # If the list is empty, give a friendly message
        classes = ["No classes scheduled right now."]

    return jsonify({"status": "success", "classes": classes}), 200

if __name__ == '__main__':
    print("=== SERVER LISTENING ON PORT 5000 ===")
    app.run(host='0.0.0.0', port=5000)
