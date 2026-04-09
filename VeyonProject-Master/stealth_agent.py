import socket
import time
import requests

# --- CONFIGURATION ---
MASTER_IP = "10.211.55.9" 
SERVER_URL = f"http://{MASTER_IP}:5000/api/heartbeat"
INTERVAL = 30  
MACHINE_ID = socket.gethostname()  

def get_local_ip():
    """ Silently gets the true local IP address """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def send_heartbeat():
    """ Silently sends the payload to the server """
    current_ip = get_local_ip()
    
    payload = {
        "machine_id": MACHINE_ID, 
        "name": MACHINE_ID, 
        "ip": current_ip,
        "username": "student",  
        "status": "online"
    }

    try:
        # Send heartbeat. If it fails, do nothing (stay stealthy)
        requests.post(SERVER_URL, json=payload, timeout=5)
    except:
        pass 

if __name__ == "__main__":
    # Infinite silent loop
    while True:
        try:
            send_heartbeat()
        except:
            pass # Never crash
            
        time.sleep(INTERVAL)