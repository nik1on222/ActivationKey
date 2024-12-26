import hashlib
import os
import time
from datetime import datetime, timedelta
import customtkinter as ctk
import sqlite3
import random
from tkinter import messagebox

# Constants
HOSTING_URL = ""  # Replace with your hosting URL
SECRET_KEY = ""  # Replace with your secret key
DATABASE_FILE = "keys.db"
KEYS_FILE = "keys.txt"

# Initialize Database
def initialize_database():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS keys")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            hardware_id TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Update Database Structure
def update_database_structure():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE keys ADD COLUMN hardware_id TEXT")
    except sqlite3.OperationalError as e:
        print("Column 'hardware_id' already exists:", e)
    conn.commit()
    conn.close()

# Functions
def generate_hardware_id():
    hardware_info = os.getenv('COMPUTERNAME') + os.getenv('USERDOMAIN')
    return hashlib.sha256(hardware_info.encode()).hexdigest()

def activate_key(key, hardware_id):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT expiry_date, hardware_id FROM keys WHERE key = ?", (key,))
    result = cursor.fetchone()
    conn.close()

    if result:
        expiry_date, registered_hardware_id = result
        if registered_hardware_id == hardware_id:
            return {"success": True, "expiry_date": expiry_date}
        else:
            return {"success": False, "message": "Hardware mismatch."}
    else:
        return {"success": False, "message": "Invalid key."}

def check_key_expiry(expiry_date):
    if datetime.now() > datetime.strptime(expiry_date, '%Y-%m-%d %H:%M:%S'):
        return True
    return False

def exit_if_expired(expiry_date):
    if check_key_expiry(expiry_date):
        root.destroy()
        exit()

# GUI Functions
def on_activate():
    key = key_entry.get()
    hardware_id = generate_hardware_id()
    activation_result = activate_key(key, hardware_id)

    if activation_result["success"]:
        expiry_date = activation_result["expiry_date"]
        expiry_label.configure(text=f"Key activated. Expires on: {expiry_date}")

        def check_expiry_loop():
            while True:
                exit_if_expired(expiry_date)
                time.sleep(60)  # Check every minute

        import threading
        threading.Thread(target=check_expiry_loop, daemon=True).start()
    else:
        expiry_label.configure(text=f"Activation failed: {activation_result['message']}")
        messagebox.showerror("Activation Failed", activation_result['message'])

def save_key_to_database_and_file(key, expiry_date, hardware_id):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO keys (key, expiry_date, hardware_id) VALUES (?, ?, ?)", (key, expiry_date, hardware_id))
    conn.commit()
    conn.close()

    with open(KEYS_FILE, "a") as f:
        f.write(f"Key: {key} | Expires on: {expiry_date} | Hardware ID: {hardware_id}\n")

# Generate Keys Function
def generate_key(days_valid):
    expiry_date = (datetime.now() + timedelta(days=days_valid)).strftime('%Y-%m-%d %H:%M:%S')
    raw_key = f"{SECRET_KEY}{expiry_date}{os.urandom(16)}"
    key = hashlib.sha256(raw_key.encode()).hexdigest()
    hardware_id = generate_hardware_id()
    save_key_to_database_and_file(key, expiry_date, hardware_id)
    return key, expiry_date

if __name__ == "__main__":
    initialize_database()
    update_database_structure()
    print("Generated Keys:")
    for days in [7, 30, 90]:
        key, expiry = generate_key(days)
        print(f"Key: {key} | Expires on: {expiry}")


# Main GUI
root = ctk.CTk()
root.geometry("600x400")
root.title("Key Activation")

# Set default theme to Dark
ctk.set_appearance_mode("dark")

# Settings
def open_settings():
    settings_window = ctk.CTkToplevel(root)
    settings_window.title("Settings")
    settings_window.geometry("400x300")

    def change_theme(theme):
        ctk.set_appearance_mode(theme)

    def change_language(lang):
        print(f"Language changed to {lang}")

    ctk.CTkLabel(settings_window, text="Theme:").pack(pady=5)
    ctk.CTkButton(settings_window, text="Light", command=lambda: change_theme("light")).pack()
    ctk.CTkButton(settings_window, text="Dark", command=lambda: change_theme("dark")).pack()

    ctk.CTkLabel(settings_window, text="Language:").pack(pady=5)
    ctk.CTkButton(settings_window, text="English", command=lambda: change_language("en")).pack()
    ctk.CTkButton(settings_window, text="Russian", command=lambda: change_language("ru")).pack()

settings_button = ctk.CTkButton(root, text="⚙️", command=open_settings, width=30, height=30, corner_radius=15)
settings_button.place(x=10, y=10)

# Key input and activation button
ctk.CTkLabel(root, text="Enter your activation key:").pack(pady=10)
key_entry = ctk.CTkEntry(root, width=300, placeholder_text="Enter Key Here", corner_radius=10)
key_entry.pack(pady=10)

activate_button = ctk.CTkButton(root, text="Activate", command=on_activate, width=200, height=40, corner_radius=10)
activate_button.pack(pady=10)

expiry_label = ctk.CTkLabel(root, text="")
expiry_label.pack(pady=10)

root.mainloop()
