import subprocess
import requests
import sys
import time

# --- CONFIGURATION ---
VEYON_CLI_PATH = r"C:\Program Files\Veyon\veyon-cli.exe"
API_URL = "http://localhost:5000/api/list_students"

def fetch_online_students():
    print(f"Connecting to API: {API_URL}...")
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []

def run_veyon_cmd(args, label):
    full_cmd = [VEYON_CLI_PATH] + args
    print(f"Executing: {label}...")
    result = subprocess.run(full_cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(" -> Success")
    else:
        # Hide "already exists" errors to keep it clean
        err = result.stderr.strip()
        if "already exists" in err or "found" in err or "exist" in err:
             print(" -> Note: OK (Ignored)")
        else:
             print(f" -> ERROR: {err}")

def restart_veyon_service():
    """Restarts the service to remove 'Ghost' rooms from the Veyon Master view."""
    print("WIN SERVICE: Restarting VeyonService to apply changes...")
    subprocess.run("net stop VeyonService", shell=True, capture_output=True)
    time.sleep(2)
    subprocess.run("net start VeyonService", shell=True, capture_output=True)
    print("WIN SERVICE: Done.")

def start_session(session_name, students):
    # 1. Create the Room
    run_veyon_cmd(["networkobjects", "add", "location", session_name], "Ensure Location Exists")
    
    # 2. Add Students
    for student in students:
        run_veyon_cmd([
            "networkobjects", "add", "computer",
            student["name"], student["ip"], "00:00:00:00:00:00", session_name
        ], f"Add Student {student['name']}")

def end_session(session_name, students):
    print(f"\n=== ENDING CLASS: {session_name} ===")
    
    # 1. Delete Computers First
    for student in students:
        run_veyon_cmd(["networkobjects", "remove", "computer", student["name"]], "Remove Computer")
    
    # 2. Delete Room
    run_veyon_cmd(["networkobjects", "remove", "location", session_name], "Remove Location")
    
    # 3. Restart Service (Crucial step)
    restart_veyon_service()

if __name__ == "__main__":
    print("\n--- NEW SESSION SETUP ---")
    user_input = input("Enter the Class Name (e.g. calc_2): ")
    CLASS_SECTION = user_input.strip().replace(" ", "-")
    
    if not CLASS_SECTION:
        print("Error: Name required.")
        sys.exit(1)
    
    # 1. Initial Start
    online_students = fetch_online_students()
    start_session(CLASS_SECTION, online_students)

    # 2. The Control Loop
    while True:
        print(f"\n[OPTIONS] Class '{CLASS_SECTION}' is Running")
        print("  Type 's' -> Show connected students")
        print("  Type 'r' -> Refresh (Add late students)")
        print("  Type 'q' -> Quit (End Class)")
        
        cmd = input("Command: ").lower().strip()
        
        if cmd == 'q':
            break # Exit loop
        
        elif cmd == 's':
            print(f" -> Server sees {len(online_students)} student(s).")
            for s in online_students:
                print(f"    [+] {s['name']} ({s['ip']})")
                
        elif cmd == 'r':
            print("Refreshing...")
            new_list = fetch_online_students()
            online_students = new_list # Update our list
            start_session(CLASS_SECTION, online_students) # Add any new ones
            print(" -> Done. (Restart Veyon Master to see new icons)")

    # 3. Cleanup
    end_session(CLASS_SECTION, online_students)