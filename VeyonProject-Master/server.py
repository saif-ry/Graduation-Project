from flask import Flask, request, jsonify

app = Flask(__name__)

# Live list of online students
online_students = {}

@app.route('/')
def home():
    return "Central Server is Running!"

# Students send their IP here
@app.route('/api/heartbeat', methods=['POST'])
def receive_heartbeat():
    data = request.json
    machine_id = data.get('machine_id')
    ip = data.get('ip')
    
    if machine_id and ip:
        # Save or update the student
        online_students[machine_id] = ip
        return jsonify({"status": "ok"}), 200
    return jsonify({"error": "missing data"}), 400

# Master script asks for the list here
@app.route('/api/list_students', methods=['GET'])
def list_students():
    student_list = []
    for name, ip in online_students.items():
        student_list.append({"name": name, "ip": ip, "mac": ""})
    return jsonify(student_list)

if __name__ == '__main__':
    print("=== SERVER LISTENING ON PORT 5000 ===")
    app.run(host='0.0.0.0', port=5000)