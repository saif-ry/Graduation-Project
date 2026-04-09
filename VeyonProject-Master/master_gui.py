import customtkinter as ctk
import requests
import subprocess
import time
import threading
import sys
import os
import platform

# --- OS DETECTION & CONFIGURATION ---
OS_TYPE = platform.system() 

MASTER_IP = "10.211.55.9"
SERVER_URL = f"http://{MASTER_IP}:5000/api/list_students"
KEY_URL = f"http://{MASTER_IP}:5000/api/get_key"
CLASSES_URL = f"http://{MASTER_IP}:5000/api/get_classes" 

if OS_TYPE == "Windows":
    import ctypes
    VEYON_CLI = r"C:\Program Files\Veyon\veyon-cli.exe"
    VEYON_DATA_DIR = r"C:\VeyonData"
    TEMP_KEY_PATH = r"C:\VeyonData\temp_teacher_private.pem"
    DB_FILE = r"C:\VeyonData\networkobjects.xml"
else:
    VEYON_CLI = "/usr/bin/veyon-cli"
    VEYON_DATA_DIR = "/etc/veyondata"
    TEMP_KEY_PATH = "/etc/veyondata/temp_teacher_private.pem"
    DB_FILE = "/etc/veyondata/networkobjects.xml"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

def is_admin():
    if OS_TYPE == "Windows":
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    else:
        return os.geteuid() == 0

class VeyonMasterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title(f"Veyon Classroom Controller ({OS_TYPE})")
        self.geometry("700x600")
        self.resizable(False, False)
        
        self.current_class = None
        self.online_students = []
        
        # --- UI LAYOUT ---
        self.header = ctk.CTkFrame(self, height=80, fg_color="transparent")
        self.header.pack(fill="x", pady=20, padx=20)
        
        self.lbl_title = ctk.CTkLabel(self.header, text="Classroom Control Panel", font=("Roboto", 24, "bold"))
        self.lbl_title.pack(side="left")
        
        self.lbl_status = ctk.CTkLabel(self.header, text="Initializing...", text_color="#F1C40F", font=("Arial", 14))
        self.lbl_status.pack(side="right", padx=10)

        self.controls = ctk.CTkFrame(self)
        self.controls.pack(fill="x", padx=20, pady=10)
        
        self.class_dropdown = ctk.CTkOptionMenu(self.controls, values=["Loading Schedule..."], width=280)
        self.class_dropdown.pack(side="left", padx=20, pady=20)
        
        self.btn_start = ctk.CTkButton(self.controls, text="▶ START SESSION", fg_color="#2CC985", width=140, state="disabled", command=self.start_session)
        self.btn_start.pack(side="left", padx=5)
        
        self.btn_end = ctk.CTkButton(self.controls, text="⏹ END SESSION", fg_color="#C0392B", width=140, state="disabled", command=self.end_session)
        self.btn_end.pack(side="right", padx=20)

        self.ops_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.ops_frame.pack(fill="x", padx=20)
        
        self.btn_refresh = ctk.CTkButton(self.ops_frame, text="⟳ Refresh List", width=120, command=self.refresh_list, state="disabled")
        self.btn_refresh.pack(side="left")
        
        self.lbl_count = ctk.CTkLabel(self.ops_frame, text="0 Students Online", font=("Arial", 12, "bold"))
        self.lbl_count.pack(side="right", padx=10)

        self.scroll = ctk.CTkScrollableFrame(self, label_text="Live Student Connections")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=20)

        # WAIT 0.5 SECONDS, THEN SHOW LOGIN POP-UP ON MAIN THREAD
        self.after(500, self.prompt_login)

    # --- CROSS-PLATFORM COMMANDS ---
    def restart_veyon_service(self):
        if OS_TYPE == "Windows":
            subprocess.run("net stop VeyonService", shell=True, capture_output=True)
            subprocess.run("net start VeyonService", shell=True, capture_output=True)
        else:
            subprocess.run("systemctl restart veyon", shell=True, capture_output=True)

    def kill_veyon_master(self):
        if OS_TYPE == "Windows":
            subprocess.run("taskkill /f /im veyon-master.exe", shell=True, capture_output=True)
        else:
            subprocess.run("pkill veyon-master", shell=True, capture_output=True)

    def run_cmd(self, args):
        full = [VEYON_CLI] + args
        subprocess.run(full, capture_output=True)

    def log(self, msg, color="white"):
        self.lbl_status.configure(text=msg, text_color=color)
        self.update_idletasks()

    def fetch_data(self):
        try:
            r = requests.get(SERVER_URL, timeout=2)
            if r.status_code == 200:
                return r.json()
            return []
        except:
            return []

    # --- NEW: SEPARATE LOGIN PROMPT ---
    def prompt_login(self):
        self.log("Waiting for Login...", "#F1C40F")
        dialog = ctk.CTkInputDialog(text="Please enter your University ID:", title="Doctor Authentication")
        doctor_id = dialog.get_input()
        
        if not doctor_id:
            self.log("Login Cancelled.", "#E74C3C")
            self.class_dropdown.configure(values=["Access Denied"])
            return

        # NOW start the background thread and pass the ID to it
        threading.Thread(target=self.system_startup, args=(doctor_id,), daemon=True).start()

    # --- STARTUP ROUTINE (Keys + Schedule) ---
    def system_startup(self, doctor_id):
        # Task 1: Fetch the Schedule from SQL Database
        self.log(f"Fetching Schedule for {doctor_id}...", "#F1C40F")
        try:
            r_sched = requests.get(f"{CLASSES_URL}?doctor_id={doctor_id}", timeout=3)
            if r_sched.status_code == 200:
                classes = r_sched.json().get("classes", [])
                self.class_dropdown.configure(values=classes)
                if classes:
                    self.class_dropdown.set(classes[0])
            else:
                self.class_dropdown.configure(values=["Invalid ID or Schedule Error"])
        except:
            self.class_dropdown.configure(values=["Server Offline"])

        # Task 2: Configure Veyon Security
        self.log("Downloading Veyon Settings...", "#F1C40F") 
        try:
            r_key = requests.get(KEY_URL, timeout=5)
            if r_key.status_code == 200:
                key_data = r_key.json().get("key")
                
                if not os.path.exists(VEYON_DATA_DIR):
                    os.makedirs(VEYON_DATA_DIR)
                    
                with open(TEMP_KEY_PATH, "w") as f:
                    f.write(key_data)
                
                self.log("Installing Security Keys...", "#3498DB")
                self.run_cmd(["authkeys", "import", "teacher/private", TEMP_KEY_PATH])
                self.run_cmd(["config", "set", "Network/AuthenticationMethod", "1"])
                
                if os.path.exists(TEMP_KEY_PATH):
                    os.remove(TEMP_KEY_PATH)
                
                self.log("Applying Settings...", "#3498DB")
                self.restart_veyon_service()
                
                if self.class_dropdown.get() != "No classes scheduled right now.":
                    self.log(f"Welcome, Dr. {doctor_id}. System Ready.", "#2CC985")
                    self.btn_start.configure(state="normal") 
                else:
                    self.log("System Ready (No active classes)", "#F1C40F")
            else:
                self.log("Server Error: Keys Failed", "#E74C3C")
                
        except requests.exceptions.ConnectionError:
            self.log("Offline: Cannot reach server.", "#E74C3C")

    # --- ACTIONS ---
    def start_session(self):
        name = self.class_dropdown.get().replace(" ", "-").replace(":", "")
        
        if not name or name in ["Loading Schedule...", "Server Offline", "Error Loading Schedule"]:
            self.log("Error: Invalid Class Selected", "#E74C3C")
            return
            
        self.current_class = name
        self.log("Initializing Session...", "#3498DB")
        
        self.online_students = self.fetch_data()
        
        self.run_cmd(["networkobjects", "add", "location", name])
        for s in self.online_students:
            self.run_cmd(["networkobjects", "add", "computer", s['name'], s['ip'], "00:00:00:00:00:00", name])
            
        self.update_list_ui()
        self.class_dropdown.configure(state="disabled") 
        self.btn_start.configure(state="disabled")
        self.btn_end.configure(state="normal")
        self.btn_refresh.configure(state="normal")
        self.log(f"Session Active", "#2CC985")

    def refresh_list(self):
        self.log("Refreshing...", "#F1C40F")
        new_list = self.fetch_data()
        new_names = [s['name'] for s in new_list]
        
        for old_s in self.online_students:
            if old_s['name'] not in new_names:
                self.run_cmd(["networkobjects", "remove", "computer", old_s['name']])
                
        for s in new_list:
            self.run_cmd(["networkobjects", "add", "computer", s['name'], s['ip'], "00:00:00:00:00:00", self.current_class])
            
        self.online_students = new_list
        self.update_list_ui()
        self.log("List Updated", "#2CC985")

    def end_session(self):
        self.log("Stopping Session...", "#E74C3C")
        
        self.kill_veyon_master()
        
        self.log("Wiping Database...", "#E74C3C")
        self.run_cmd(["networkobjects", "clear"])
        
        self.log("Restarting Service...", "#E74C3C")
        self.restart_veyon_service()
        time.sleep(2) 
        
        self.online_students = []
        self.current_class = None
        self.update_list_ui()
        
        self.class_dropdown.configure(state="normal") 
        self.btn_start.configure(state="normal")
        self.btn_end.configure(state="disabled")
        self.btn_refresh.configure(state="disabled")
        
        self.log("Session Ended & Completely Wiped", "#2CC985")

    def update_list_ui(self):
        for widget in self.scroll.winfo_children():
            widget.destroy()
        self.lbl_count.configure(text=f"{len(self.online_students)} Students Online")
        for s in self.online_students:
            row = ctk.CTkFrame(self.scroll, fg_color="#2B2B2B")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text="🖥️", width=40).pack(side="left")
            ctk.CTkLabel(row, text=s['name'], font=("Arial", 12, "bold")).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=s['ip'], text_color="gray").pack(side="left", padx=5)
            ctk.CTkLabel(row, text="● Online", text_color="#2CC985").pack(side="right", padx=10)

if __name__ == "__main__":
    try:
        if not is_admin():
            if OS_TYPE == "Windows":
                print("Re-launching as admin...")
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            else:
                print("\n[REQUIRED] Please run this application with 'sudo' on Linux.")
                sys.exit()
        else:
            app = VeyonMasterApp()
            app.mainloop()
    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
        input("\nPress ENTER to close...")
