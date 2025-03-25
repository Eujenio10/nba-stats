import requests
import hashlib
import platform
import uuid
import os
import json
import tkinter as tk
from tkinter import messagebox

# URL dell'API, cambiare in produzione
API_URL = "http://localhost:5000"
# API_URL = "https://nba-stats-api.onrender.com" # Per produzione

def get_machine_id():
    """Genera un ID univoco per il dispositivo basato su hardware e sistema operativo."""
    # Otteniamo i dati hardware per generare un ID univoco
    system_info = platform.uname()
    
    # Creiamo un hash del nome nodo (hostname) e altre info hardware
    machine_data = f"{system_info.node}-{system_info.system}-{system_info.processor}"
    
    try:
        # Su Windows, possiamo usare il serial del volume C:
        if system_info.system == 'Windows':
            import subprocess
            result = subprocess.check_output('wmic csproduct get UUID', shell=True).decode()
            uuid_result = result.split('\n')[1].strip()
            machine_data += f"-{uuid_result}"
    except:
        pass
        
    # Generiamo un hash SHA-256 dell'identificatore
    machine_id = hashlib.sha256(machine_data.encode()).hexdigest()
    return machine_id

def save_api_key(api_key):
    """Salva la chiave API in un file locale."""
    config_dir = os.path.join(os.path.expanduser("~"), ".nba-stats")
    os.makedirs(config_dir, exist_ok=True)
    
    with open(os.path.join(config_dir, "config.json"), "w") as f:
        json.dump({"api_key": api_key}, f)

def load_api_key():
    """Carica la chiave API dal file locale."""
    config_file = os.path.join(os.path.expanduser("~"), ".nba-stats", "config.json")
    
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            config = json.load(f)
            return config.get("api_key")
    
    return None

def verify_api_key(api_key):
    """Verifica se la chiave API è valida."""
    machine_id = get_machine_id()
    
    try:
        response = requests.post(
            f"{API_URL}/api/verify-key",
            json={"key": api_key, "machine_id": machine_id},
            timeout=10
        )
        
        return response.status_code == 200, response.json()
    except Exception as e:
        print(f"Errore durante la verifica della chiave: {e}")
        return False, {"error": str(e)}

def get_stats_data(endpoint, api_key):
    """Ottiene i dati dalle API, utilizzando la chiave API."""
    machine_id = get_machine_id()
    
    try:
        response = requests.get(
            f"{API_URL}{endpoint}",
            headers={
                "X-API-Key": api_key,
                "X-Machine-ID": machine_id
            },
            timeout=15
        )
        
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, response.json()
    except Exception as e:
        print(f"Errore durante la richiesta a {endpoint}: {e}")
        return False, {"error": str(e)}

class LoginApp:
    def __init__(self, root):
        self.root = root
        root.title("NBA Stats - Login")
        root.geometry("400x300")
        root.configure(bg="#ffffff")
        
        # Frame principale
        self.main_frame = tk.Frame(root, bg="#ffffff")
        self.main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Logo o titolo
        tk.Label(
            self.main_frame, 
            text="NBA Stats", 
            font=("Helvetica", 24, "bold"),
            bg="#ffffff",
            fg="#1e90ff"
        ).pack(pady=20)
        
        # Frame per il form
        form_frame = tk.Frame(self.main_frame, bg="#ffffff")
        form_frame.pack(pady=10)
        
        # Campo per la chiave API
        tk.Label(
            form_frame, 
            text="Inserisci la tua chiave API:",
            font=("Helvetica", 12),
            bg="#ffffff"
        ).pack(anchor="w")
        
        self.api_key_entry = tk.Entry(form_frame, width=40, font=("Helvetica", 12))
        self.api_key_entry.pack(pady=5, fill="x")
        
        # Carica la chiave salvata, se presente
        saved_key = load_api_key()
        if saved_key:
            self.api_key_entry.insert(0, saved_key)
            # Verifica automaticamente la chiave all'avvio
            self.verify_key()
        
        # Pulsante di login
        login_button = tk.Button(
            form_frame,
            text="Accedi",
            font=("Helvetica", 12, "bold"),
            bg="#1e90ff",
            fg="#ffffff",
            bd=0,
            padx=20,
            pady=8,
            command=self.verify_key
        )
        login_button.pack(pady=20)
    
    def verify_key(self):
        # Ottieni la chiave inserita
        api_key = self.api_key_entry.get().strip()
        
        if not api_key:
            messagebox.showerror("Errore", "Inserisci una chiave API valida")
            return
        
        # Mostra un messaggio di caricamento
        self.main_frame.config(cursor="wait")
        self.root.update()
        
        # Verifica la chiave
        is_valid, response = verify_api_key(api_key)
        
        # Ripristina il cursore
        self.main_frame.config(cursor="")
        
        if is_valid:
            # Salva la chiave
            save_api_key(api_key)
            
            # Mostra il messaggio di successo
            expiry_date = response.get("expiry_date", "sconosciuta")
            messagebox.showinfo(
                "Accesso riuscito", 
                f"Benvenuto! La tua chiave è valida fino al {expiry_date}."
            )
            
            # Qui apriresti la finestra principale dell'app
            # main_window = MainApp(tk.Toplevel())
            # self.root.withdraw()
        else:
            error_msg = response.get("error", "Errore sconosciuto")
            messagebox.showerror("Errore", f"Chiave non valida: {error_msg}")

if __name__ == "__main__":
    root = tk.Tk()
    app = LoginApp(root)
    root.mainloop() 