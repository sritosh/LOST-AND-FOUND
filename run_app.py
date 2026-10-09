"""
Campus Lost & Found System - Application Launcher
Launches the Flask backend server and automatically opens the browser.
Authors: Sritosh Rath (24BDS0001) & Jayant Sharma (24BAI0148)
"""

import os
import sys
import webbrowser
import threading
import time

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from app import app, init_db

def open_browser():
    """Opens browser after server starts."""
    time.sleep(1.2)
    url = "http://127.0.0.1:5000"
    print(f"\n[INFO] Opening application in browser: {url}\n")
    webbrowser.open(url)

if __name__ == '__main__':
    print("\n" + "="*65)
    print("  CAMPUS LOST & FOUND SYSTEM - DBMS LAB PROJECT")
    print("  Team: Sritosh Rath (24BDS0001) & Jayant Sharma (24BAI0148)")
    print("  Milestone: Review 1 (50% Progress Demonstration)")
    print("="*65 + "\n")

    # Ensure DB is ready
    print("[1/3] Initializing SQLite / MySQL Database Schema & Sample Data...")
    init_db()
    print("[2/3] Database successfully prepared with 6 normalized 3NF tables!")
    
    # Launch browser thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    print("[3/3] Starting REST API & Web UI Server on http://127.0.0.1:5000...")
    print("Press Ctrl+C in this terminal to stop the server.\n")
    app.run(host='127.0.0.1', port=5000, debug=False)
